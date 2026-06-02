"""
数据管理模块 (成员 B)
- 读取单细胞数据 (.h5ad / AnnData)
- 数据格式校验与基础预处理
- 将细胞表示为向量，输出给索引构建模块
- 配合成员 C 实现数据集的增删管理
"""

import scanpy as sc
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import warnings
warnings.filterwarnings("ignore")


class DataManager:
    """单细胞数据管理器：读取、校验、基础信息查询、向量输出"""

    def __init__(self, filepath: str = "liver.h5ad"):
        self.filepath = Path(filepath)
        self.adata: Optional[sc.AnnData] = None
        self._loaded = False

    # ---------- 1. 读取数据 ----------
    def load_data(self) -> sc.AnnData:
        """读取 .h5ad 文件"""
        if not self.filepath.exists():
            raise FileNotFoundError(f"数据文件不存在: {self.filepath}")

        print(f"[DataManager] 正在读取 {self.filepath} ...")
        self.adata = sc.read_h5ad(self.filepath)
        self._loaded = True
        print(f"[DataManager] 读取完成: {self.adata.n_obs} 细胞 × {self.adata.n_vars} 基因")
        return self.adata

    # ---------- 2. 数据格式校验 ----------
    def validate_data(self) -> bool:
        """校验数据格式完整性"""
        if self.adata is None:
            raise ValueError("请先调用 load_data() 加载数据")

        checks = {}
        # 必须存在的字段
        checks["X (表达矩阵)"] = self.adata.X is not None
        checks["obs (细胞元数据)"] = self.adata.obs is not None
        checks["var (基因元数据)"] = self.adata.var is not None

        # 关键 obs 列
        required_obs = ["cell_type", "disease", "AgeGroup"]
        for col in required_obs:
            checks[f"obs['{col}']"] = col in self.adata.obs.columns

        # 降维结果
        for key in ["X_pca", "X_umap"]:
            checks[f"obsm['{key}']"] = key in self.adata.obsm

        print("\n[DataManager] ===== 数据校验结果 =====")
        all_ok = True
        for name, ok in checks.items():
            status = "✓" if ok else "✗ 缺失!"
            if not ok:
                all_ok = False
            print(f"  {status} {name}")
        print(f"[DataManager] 校验{'通过' if all_ok else '未通过，请检查数据'}")
        return all_ok

    # ---------- 3. 数据摘要 ----------
    def summary(self) -> Dict:
        """返回数据摘要信息"""
        adata = self.adata
        return {
            "n_cells": adata.n_obs,
            "n_genes": adata.n_vars,
            "cell_types": adata.obs["cell_type"].value_counts().to_dict(),
            "disease_types": adata.obs["disease"].value_counts().to_dict(),
            "age_groups": adata.obs["AgeGroup"].value_counts().to_dict(),
            "pca_dims": adata.obsm["X_pca"].shape if "X_pca" in adata.obsm else None,
            "umap_dims": adata.obsm["X_umap"].shape if "X_umap" in adata.obsm else None,
            "obs_columns": adata.obs.columns.tolist(),
            "var_columns": adata.var.columns.tolist(),
        }

    # ---------- 4. 获取原始表达矩阵 ----------
    def get_expression_matrix(self) -> np.ndarray:
        """返回原始表达矩阵 (n_cells, n_genes)"""
        if self.adata.X is None:
            raise ValueError("表达矩阵为空")
        # 处理稀疏矩阵
        if hasattr(self.adata.X, "toarray"):
            return self.adata.X.toarray()
        return np.array(self.adata.X)

    # ---------- 5. 获取 PCA 向量（供索引构建） ----------
    def get_pca_vectors(self, n_dims: int = 64) -> np.ndarray:
        """
        获取 PCA 降维向量，供成员 A 构建索引
        返回: (n_cells, n_dims) float32 数组
        """
        if "X_pca" not in self.adata.obsm:
            raise ValueError("数据中未找到 PCA 降维结果 (obsm['X_pca'])")

        pca = self.adata.obsm["X_pca"]
        actual_dims = min(n_dims, pca.shape[1])
        vectors = pca[:, :actual_dims].astype(np.float32)
        print(f"[DataManager] PCA 向量: {vectors.shape}, dtype={vectors.dtype}")
        return vectors

    # ---------- 6. 导出向量给成员 A ----------
    def export_vectors_for_index(self, output_path: str = "cell_vectors.npy",
                                  n_dims: int = 64) -> str:
        """导出 PCA 向量为 .npy 文件，供成员 A 构建 ANN 索引"""
        vectors = self.get_pca_vectors(n_dims)
        np.save(output_path, vectors)
        print(f"[DataManager] 向量已导出: {output_path}, shape={vectors.shape}")
        return output_path

    # ---------- 7. 导出元数据供成员 C/D ----------
    def export_metadata(self, output_path: str = "cell_metadata.csv") -> str:
        """导出细胞元数据为 CSV，供前端展示"""
        # 精选关键列
        key_cols = ["cell_type", "disease", "AgeGroup", "donor_age", "sex",
                     "nCount_RNA", "nFeature_RNA", "percent.mt", "Phase"]
        available = [c for c in key_cols if c in self.adata.obs.columns]
        meta = self.adata.obs[available].copy()
        meta.to_csv(output_path, index_label="cell_index")
        print(f"[DataManager] 元数据已导出: {output_path}, columns={available}")
        return output_path

    # ---------- 8. 导出 2D 坐标供成员 D 可视化 ----------
    def export_2d_coords(self, method: str = "umap",
                          output_path: str = "cell_2d_coords.csv") -> str:
        """导出细胞 2D 坐标（UMAP 或 PCA 前两维），供 D 绘制细胞分布图"""
        key = f"X_{method}"
        if key not in self.adata.obsm:
            print(f"[DataManager] 未找到 {key}，使用 X_pca 前两维")
            key = "X_pca"

        coords = self.adata.obsm[key][:, :2]
        df = pd.DataFrame(coords, columns=[f"{method}_1", f"{method}_2"])
        df["cell_type"] = self.adata.obs["cell_type"].values
        df["disease"] = self.adata.obs["disease"].values
        df["AgeGroup"] = self.adata.obs["AgeGroup"].values
        df.to_csv(output_path, index_label="cell_index")
        print(f"[DataManager] 2D 坐标已导出: {output_path}")
        return output_path

    # ---------- 9. 数据集增删管理接口 ----------
    def get_cells_by_filter(self, filters: Dict[str, str]) -> np.ndarray:
        """根据条件过滤，返回符合条件的细胞索引"""
        mask = np.ones(self.adata.n_obs, dtype=bool)
        for col, val in filters.items():
            if col in self.adata.obs.columns:
                mask &= (self.adata.obs[col].values == val)
            else:
                print(f"[DataManager] 警告: 列 '{col}' 不存在，跳过此过滤条件")
        indices = np.where(mask)[0]
        print(f"[DataManager] 过滤 '{filters}': {len(indices)} 个细胞匹配")
        return indices

    def add_cells(self, new_adata: sc.AnnData) -> None:
        """新增细胞数据（预留接口）"""
        self.adata = sc.concat([self.adata, new_adata], axis=0)
        print(f"[DataManager] 已追加 {new_adata.n_obs} 个细胞，总计 {self.adata.n_obs}")

    def remove_cells(self, indices: np.ndarray) -> None:
        """删除指定索引的细胞（预留接口）"""
        keep = np.ones(self.adata.n_obs, dtype=bool)
        keep[indices] = False
        self.adata = self.adata[keep].copy()
        print(f"[DataManager] 已删除 {len(indices)} 个细胞，剩余 {self.adata.n_obs}")

    def get_cell_info(self, index: int) -> Dict:
        """获取单个细胞的详细信息"""
        info = {
            "cell_index": index,
            "cell_type": str(self.adata.obs["cell_type"].iloc[index]),
            "disease": str(self.adata.obs["disease"].iloc[index]),
            "AgeGroup": str(self.adata.obs["AgeGroup"].iloc[index]),
        }
        # 添加更多可用字段
        for col in ["donor_age", "sex", "nCount_RNA", "nFeature_RNA", "percent.mt"]:
            if col in self.adata.obs.columns:
                info[col] = str(self.adata.obs[col].iloc[index])
        return info


# ===== 测试入口 =====
if __name__ == "__main__":
    dm = DataManager("liver.h5ad")
    dm.load_data()
    dm.validate_data()

    summary = dm.summary()
    print(f"\n细胞类型数: {len(summary['cell_types'])}")
    print(f"PCA 维度: {summary['pca_dims']}")

    # 导出向量和元数据
    dm.export_vectors_for_index("cell_vectors.npy", n_dims=64)
    dm.export_metadata("cell_metadata.csv")
    dm.export_2d_coords("umap", "cell_2d_coords.csv")
    print("\n[DataManager] 所有导出完成!")
