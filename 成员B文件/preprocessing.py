"""
数据处理与降维模块 (成员 B)
- 质量控制 (QC)：过滤低质量细胞
- 数据标准化 + 对数变换
- 高变基因筛选
- 数据缩放
- PCA 降维：生成低维细胞向量
"""

import scanpy as sc
import numpy as np
from typing import Optional, Tuple
import warnings
warnings.filterwarnings("ignore")


class Preprocessor:
    """单细胞数据预处理流水线"""

    def __init__(self, adata: sc.AnnData):
        """
        Args:
            adata: AnnData 对象 (原始数据)
        """
        self.adata = adata.copy()  # 不修改原始数据
        self.raw_adata = adata      # 保留原始引用
        self._qc_passed: Optional[np.ndarray] = None

    # ---------- 1. 质量控制 (QC) ----------
    def quality_control(self,
                         min_genes: int = 200,
                         max_genes: Optional[int] = None,
                         min_cells: int = 3,
                         max_pct_mt: float = 20.0,
                         filter_genes: bool = True) -> sc.AnnData:
        """
        QC 过滤:
        - 过滤表达基因数过少的细胞
        - 过滤线粒体基因比例过高的细胞
        - 过滤在极少细胞中表达的基因

        Args:
            min_genes: 细胞至少表达的基因数
            max_genes: 细胞最多表达的基因数 (None=自动计算)
            min_cells: 基因至少在几个细胞中表达
            max_pct_mt: 最大线粒体基因百分比
            filter_genes: 是否过滤低表达基因
        """
        print("\n[Preprocessor] ===== 质量控制 (QC) =====")
        print(f"  QC 前: {self.adata.n_obs} 细胞, {self.adata.n_vars} 基因")

        # 计算 QC 指标
        if "percent.mt" not in self.adata.obs.columns:
            # 尝试识别线粒体基因 (MT- 开头)
            mt_mask = self.adata.var_names.str.startswith("MT-")
            if mt_mask.sum() > 0:
                self.adata.obs["percent.mt"] = np.sum(
                    self.adata[:, mt_mask].X.toarray()
                    if hasattr(self.adata[:, mt_mask].X, "toarray")
                    else self.adata[:, mt_mask].X,
                    axis=1
                ) / np.sum(self.adata.X.toarray() if hasattr(self.adata.X, "toarray") else self.adata.X, axis=1) * 100
            else:
                self.adata.obs["percent.mt"] = 0.0
                print("  未检测到线粒体基因 (MT-)，跳过 MT 过滤")

        # 计算每个细胞的基因数
        if "nFeature_RNA" not in self.adata.obs.columns:
            self.adata.obs["nFeature_RNA"] = np.sum(
                self.adata.X.toarray() > 0 if hasattr(self.adata.X, "toarray")
                else self.adata.X > 0, axis=1
            )

        # 自动计算 max_genes 阈值 (mean + 3*std)
        if max_genes is None:
            mean_genes = self.adata.obs["nFeature_RNA"].mean()
            std_genes = self.adata.obs["nFeature_RNA"].std()
            max_genes = int(mean_genes + 3 * std_genes)
            print(f"  自动 max_genes 阈值: {max_genes}")

        # 应用细胞过滤
        keep_cells = (
            (self.adata.obs["nFeature_RNA"] >= min_genes) &
            (self.adata.obs["nFeature_RNA"] <= max_genes) &
            (self.adata.obs["percent.mt"] <= max_pct_mt)
        )
        n_removed = (~keep_cells).sum()
        self.adata = self.adata[keep_cells].copy()
        print(f"  过滤低质量细胞: 移除 {n_removed} 个, 保留 {self.adata.n_obs} 个")

        # 过滤低表达基因
        if filter_genes:
            sc.pp.filter_genes(self.adata, min_cells=min_cells)
            print(f"  过滤低表达基因后: {self.adata.n_vars} 个基因")

        self._qc_passed = keep_cells
        return self.adata

    # ---------- 2. 数据标准化 + 对数变换 ----------
    def normalize(self, target_sum: float = 1e4) -> sc.AnnData:
        """
        文库大小标准化 + log1p 变换
        """
        print("\n[Preprocessor] ===== 标准化 & 对数变换 =====")
        print(f"  标准化前: mean={self.adata.X.mean():.2f}")

        # 标准化到每细胞 10,000 reads
        sc.pp.normalize_total(self.adata, target_sum=target_sum)
        print(f"  标准化后 (target_sum={target_sum}): mean={self.adata.X.mean():.2f}")

        # log1p 变换
        sc.pp.log1p(self.adata)
        print(f"  log1p 变换后: mean={self.adata.X.mean():.4f}")

        # 保存原始计数到 raw
        self.adata.raw = self.adata.copy()
        return self.adata

    # ---------- 3. 高变基因筛选 ----------
    def select_highly_variable_genes(self,
                                      n_top_genes: int = 2000,
                                      flavor: str = "seurat") -> sc.AnnData:
        """
        筛选高变基因 (HVG)

        Args:
            n_top_genes: 保留的高变基因数
            flavor: 方法 ('seurat', 'seurat_v3', 'cell_ranger')
                    注: seurat_v3 需要 scikit-misc, 若未安装自动回退到 seurat
        """
        print(f"\n[Preprocessor] ===== 高变基因筛选 (top {n_top_genes}, {flavor}) =====")

        # 尝试使用指定方法, 失败则回退
        try:
            sc.pp.highly_variable_genes(
                self.adata, n_top_genes=n_top_genes, flavor=flavor
            )
        except (ModuleNotFoundError, ImportError) as e:
            print(f"  {flavor} 不可用 ({e}), 回退到 'seurat'")
            sc.pp.highly_variable_genes(
                self.adata, n_top_genes=n_top_genes, flavor="seurat"
            )

        n_hvg = self.adata.var["highly_variable"].sum()
        print(f"  高变基因数: {n_hvg}")

        # 保留高变基因
        self.adata = self.adata[:, self.adata.var["highly_variable"]].copy()
        print(f"  筛选后: {self.adata.n_obs} 细胞 × {self.adata.n_vars} 基因")
        return self.adata

    # ---------- 4. 数据缩放 ----------
    def scale_data(self, max_value: float = 10.0) -> sc.AnnData:
        """
        Z-score 缩放 (每基因), 裁剪到 [-max_value, max_value]
        """
        print(f"\n[Preprocessor] ===== 数据缩放 (max_value={max_value}) =====")
        sc.pp.scale(self.adata, max_value=max_value)
        print(f"  缩放后: mean={self.adata.X.mean():.4f}, std={self.adata.X.std():.4f}")
        return self.adata

    # ---------- 5. PCA 降维 ----------
    def run_pca(self,
                n_comps: int = 64,
                svd_solver: str = "arpack",
                random_state: int = 42) -> np.ndarray:
        """
        PCA 降维，生成低维细胞向量

        Args:
            n_comps: PCA 主成分数 (输出维度)
            svd_solver: SVD 求解器
            random_state: 随机种子

        Returns:
            (n_cells, n_comps) PCA 向量, float32
        """
        print(f"\n[Preprocessor] ===== PCA 降维 (n_comps={n_comps}) =====")
        sc.tl.pca(self.adata, n_comps=n_comps, svd_solver=svd_solver,
                   random_state=random_state)

        pca_vectors = self.adata.obsm["X_pca"].astype(np.float32)
        variance_ratio = self.adata.uns["pca"]["variance_ratio"]
        cum_var = np.cumsum(variance_ratio)

        print(f"  PCA 向量 shape: {pca_vectors.shape}")
        print(f"  前 {n_comps} 个主成分解释方差比: {cum_var[-1]:.2%}")
        print(f"  前 5 个主成分分别解释: {[f'{v:.2%}' for v in variance_ratio[:5]]}")

        return pca_vectors

    # ---------- 6. 完整流水线 ----------
    def run_full_pipeline(self,
                           n_top_genes: int = 2000,
                           n_pca_comps: int = 64,
                           min_genes: int = 200,
                           max_pct_mt: float = 20.0,
                           scale_max_value: float = 10.0,
                           hv_flavor: str = "seurat") -> Tuple[sc.AnnData, np.ndarray]:
        """
        运行完整预处理流水线:
        QC → 标准化 → log变换 → HVG → 缩放 → PCA

        Args:
            n_top_genes: 高变基因数
            n_pca_comps: PCA 主成分数
            min_genes: QC 最小基因数
            max_pct_mt: 最大线粒体百分比
            scale_max_value: 缩放裁剪值
            hv_flavor: 高变基因筛选方法 ('seurat'/'seurat_v3'/'cell_ranger')

        Returns:
            (处理后的 AnnData, PCA 向量)
        """
        print("=" * 60)
        print("  单细胞数据预处理流水线")
        print("=" * 60)

        self.quality_control(min_genes=min_genes, max_pct_mt=max_pct_mt)
        self.normalize()
        self.select_highly_variable_genes(n_top_genes=n_top_genes, flavor=hv_flavor)
        self.scale_data(max_value=scale_max_value)
        pca_vectors = self.run_pca(n_comps=n_pca_comps)

        print("\n[Preprocessor] ===== 流水线完成 =====")
        print(f"  最终数据: {self.adata.n_obs} 细胞 × {self.adata.n_vars} 基因")
        print(f"  PCA 向量: {pca_vectors.shape}, dtype={pca_vectors.dtype}")
        return self.adata, pca_vectors

    # ---------- 7. 获取处理后的向量 ----------
    def get_processed_vectors(self) -> np.ndarray:
        """获取处理后的 PCA 向量"""
        if "X_pca" not in self.adata.obsm:
            raise ValueError("请先运行 run_pca()")
        return self.adata.obsm["X_pca"].astype(np.float32)

    # ---------- 8. 解释方差 ----------
    def get_variance_explained(self) -> np.ndarray:
        """获取 PCA 各主成分的方差解释率"""
        if "pca" not in self.adata.uns:
            raise ValueError("请先运行 run_pca()")
        return self.adata.uns["pca"]["variance_ratio"]


# ===== 测试入口 =====
if __name__ == "__main__":
    import scanpy as sc

    adata = sc.read_h5ad("liver.h5ad")
    print(f"原始数据: {adata.n_obs} cells, {adata.n_vars} genes")

    preprocessor = Preprocessor(adata)
    adata_processed, pca_vecs = preprocessor.run_full_pipeline(
        n_top_genes=2000,
        n_pca_comps=64,
        hv_flavor="seurat"  # 使用 seurat 避免 scikit-misc 依赖
    )

    # 保存结果
    np.save("processed_cell_vectors.npy", pca_vecs)
    print("\nPCA 向量已保存到 processed_cell_vectors.npy")
