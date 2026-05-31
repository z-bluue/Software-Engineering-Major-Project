"""
查询检索模块 (成员 B)
- Top-K 相似细胞检索 (中期必须)
- 支持多种距离度量 (余弦相似度/欧氏距离)
- 支持 ANN 加速检索 (FAISS / HNSW)
- 条件过滤检索 (结项必须)
- 配合成员 C 封装检索接口
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List, Tuple, Union
from dataclasses import dataclass, field
import time
import warnings
warnings.filterwarnings("ignore")


@dataclass
class SearchResult:
    """检索结果"""
    indices: np.ndarray          # 匹配细胞的索引 (n_queries, k)
    distances: np.ndarray        # 距离/相似度分数 (n_queries, k)
    metadata: List[List[Dict]]   # 每个查询的 k 个细胞的元数据
    query_time_ms: float         # 查询耗时 (毫秒)
    method: str                  # 检索方法


class SearchEngine:
    """
    单细胞相似检索引擎
    支持: 暴力搜索 / FAISS IVF / HNSW + 条件过滤
    """

    def __init__(self,
                 vectors: np.ndarray,
                 metadata: pd.DataFrame,
                 method: str = "faiss"):
        """
        Args:
            vectors: (n_cells, n_dims) 细胞向量, float32
            metadata: (n_cells, *) 细胞元数据 DataFrame
            method: 检索方法 ("brute", "faiss", "hnsw")
        """
        self.vectors = vectors.astype(np.float32)
        self.metadata = metadata.reset_index(drop=True)
        self.n_cells, self.n_dims = vectors.shape
        self.method = method
        self._index = None
        self._index_built = False

        # 归一化向量用于余弦相似度
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0  # 避免除 0
        self.vectors_normalized = self.vectors / norms

        print(f"[SearchEngine] 初始化: {self.n_cells} 细胞, "
              f"{self.n_dims} 维, 方法={method}")

    # ===================== 索引构建 =====================

    def build_index(self,
                    nlist: int = 100,
                    nprobe: int = 10,
                    hnsw_m: int = 16,
                    hnsw_ef_construction: int = 200) -> None:
        """
        构建 ANN 索引
        - FAISS IVF: nlist=聚类中心数, nprobe=搜索时探测的聚类数
        - HNSW: M=连接数, ef_construction=构建时搜索宽度
        """
        if self.method == "faiss":
            self._build_faiss_index(nlist, nprobe)
        elif self.method == "hnsw":
            self._build_hnsw_index(hnsw_m, hnsw_ef_construction)
        elif self.method == "brute":
            print("[SearchEngine] 暴力搜索无需构建索引")
            self._index_built = True
        else:
            raise ValueError(f"未知检索方法: {self.method}")

    def _build_faiss_index(self, nlist: int, nprobe: int) -> None:
        """构建 FAISS IVF 索引 (基于内积 = 余弦相似度)"""
        try:
            import faiss
        except ImportError:
            print("[SearchEngine] FAISS 未安装，回退到暴力搜索")
            self.method = "brute"
            self._index_built = True
            return

        # 使用内积搜索 (因已 L2 归一化, 内积 = 余弦相似度)
        quantizer = faiss.IndexFlatIP(self.n_dims)
        self._index = faiss.IndexIVFFlat(quantizer, self.n_dims, nlist,
                                          faiss.METRIC_INNER_PRODUCT)

        print(f"[SearchEngine] 训练 FAISS IVF 索引 (nlist={nlist}) ...")
        t0 = time.time()
        self._index.train(self.vectors_normalized)
        self._index.add(self.vectors_normalized)
        self._index.nprobe = nprobe
        self._index_built = True
        print(f"[SearchEngine] FAISS 索引构建完成, 耗时 {time.time()-t0:.2f}s, "
              f"nprobe={nprobe}")

    def _build_hnsw_index(self, M: int, ef_construction: int) -> None:
        """构建 HNSW 索引"""
        try:
            import hnswlib
        except ImportError:
            print("[SearchEngine] hnswlib 未安装，回退到暴力搜索")
            self.method = "brute"
            self._index_built = True
            return

        self._index = hnswlib.Index(space="cosine", dim=self.n_dims)
        self._index.init_index(
            max_elements=self.n_cells,
            ef_construction=ef_construction,
            M=M
        )
        print(f"[SearchEngine] 构建 HNSW 索引 (M={M}, ef_construction={ef_construction}) ...")
        t0 = time.time()
        self._index.add_items(self.vectors, np.arange(self.n_cells))
        self._index.set_ef(min(ef_construction, 100))  # 默认 ef
        self._index_built = True
        print(f"[SearchEngine] HNSW 索引构建完成, 耗时 {time.time()-t0:.2f}s")

    # ===================== 检索接口 =====================

    def search(self,
               query: np.ndarray,
               k: int = 10,
               filters: Optional[Dict[str, str]] = None,
               metric: str = "cosine",
               ef_search: Optional[int] = None) -> SearchResult:
        """
        Top-K 相似细胞检索 (主入口)

        Args:
            query: 查询向量, shape (n_queries, n_dims) 或 (n_dims,)
            k: 返回 top-k 个最相似细胞
            filters: 条件过滤, 如 {"cell_type": "hepatocyte", "AgeGroup": "Adult"}
            metric: 距离度量 ("cosine" 或 "euclidean")
            ef_search: HNSW 搜索宽度 (仅 HNSW 有效)

        Returns:
            SearchResult: 包含索引、距离、元数据、耗时
        """
        # 确保 query 是 2D
        if query.ndim == 1:
            query = query.reshape(1, -1)
        query = query.astype(np.float32)

        # 条件过滤: 获取候选细胞 mask
        candidate_mask = self._apply_filters(filters)

        t0 = time.time()

        # 条件过滤时: 如果候选集占比 < 30%, ANN 索引可能找不到足够匹配
        # 此时自动回退到暴力搜索以保证准确率
        if candidate_mask is not None and candidate_mask.sum() < self.n_cells * 0.3:
            indices, distances = self._brute_search(query, k, metric, candidate_mask)
            method_name = f"brute_{metric}_filtered"
        elif self.method == "brute":
            indices, distances = self._brute_search(query, k, metric, candidate_mask)
            method_name = f"brute_{metric}"
        elif self.method == "faiss":
            indices, distances = self._faiss_search(query, k, candidate_mask)
            method_name = "faiss_ivf"
        elif self.method == "hnsw":
            indices, distances = self._hnsw_search(query, k, ef_search, candidate_mask)
            method_name = "hnsw"
        else:
            raise ValueError(f"未知方法: {self.method}")

        query_time = (time.time() - t0) * 1000

        # 收集元数据
        meta_list = []
        for q_idx in range(len(query)):
            cell_metas = []
            for rank, cell_idx in enumerate(indices[q_idx]):
                if cell_idx >= 0:
                    cell_metas.append(self._get_cell_meta(cell_idx, rank, distances[q_idx][rank]))
            meta_list.append(cell_metas)

        return SearchResult(
            indices=indices,
            distances=distances,
            metadata=meta_list,
            query_time_ms=query_time,
            method=method_name
        )

    # ---------- 暴力搜索 ----------
    def _brute_search(self, query: np.ndarray, k: int, metric: str,
                       candidate_mask: Optional[np.ndarray] = None
                       ) -> Tuple[np.ndarray, np.ndarray]:
        """暴力搜索 (支持条件过滤)"""
        n_queries = len(query)

        if metric == "cosine":
            # 使用归一化向量算内积
            q_norm = query / (np.linalg.norm(query, axis=1, keepdims=True) + 1e-10)
            sim = np.dot(q_norm, self.vectors_normalized.T)  # (n_queries, n_cells)
            # 相似度越高越好
            if candidate_mask is not None:
                sim[:, ~candidate_mask] = -np.inf
            # 按相似度从高到低排序
            top_indices = np.argsort(-sim, axis=1)[:, :k]
            # 取对应相似度作为 scores
            top_scores = np.take_along_axis(sim, top_indices, axis=1)

        elif metric == "euclidean":
            # 欧氏距离
            sim = np.zeros((n_queries, self.n_cells), dtype=np.float32)
            for i in range(n_queries):
                diff = self.vectors - query[i]
                sim[i] = -np.sum(diff ** 2, axis=1)  # 负距离, 越大越好
            if candidate_mask is not None:
                sim[:, ~candidate_mask] = -np.inf
            top_indices = np.argsort(-sim, axis=1)[:, :k]
            top_scores = np.take_along_axis(sim, top_indices, axis=1)
            # 转回正距离
            top_scores = np.sqrt(-top_scores)

        else:
            raise ValueError(f"未知度量: {metric}")

        return top_indices, top_scores

    # ---------- FAISS 搜索 ----------
    def _faiss_search(self, query: np.ndarray, k: int,
                       candidate_mask: Optional[np.ndarray] = None
                       ) -> Tuple[np.ndarray, np.ndarray]:
        """FAISS IVF 搜索（条件过滤时自动回退暴力搜索以保证完整性）"""
        import faiss

        if not self._index_built:
            self.build_index()

        # 归一化查询向量
        q_norm = query / (np.linalg.norm(query, axis=1, keepdims=True) + 1e-10)

        if candidate_mask is not None:
            n_candidates = candidate_mask.sum()
            # 如果候选集很小, 或候选集占总体的比例很小, FAISS 可能找不到足够的匹配
            # 策略: 增大 search_k 为候选集的 20% 或 k*20, 取较小值
            search_k = min(max(k * 20, int(n_candidates * 0.2)), self.n_cells)
            distances, indices = self._index.search(q_norm, search_k)
            # 手动过滤
            filtered_indices = []
            filtered_distances = []
            for i in range(len(query)):
                valid = candidate_mask[indices[i]]
                fi = indices[i][valid][:k]
                fd = distances[i][valid][:k]
                # 如果不够 k, 补 -1
                if len(fi) < k:
                    fi = np.pad(fi, (0, k - len(fi)), constant_values=-1)
                    fd = np.pad(fd, (0, k - len(fd)), constant_values=-1.0)
                filtered_indices.append(fi)
                filtered_distances.append(fd)
            return np.array(filtered_indices), np.array(filtered_distances)
        else:
            distances, indices = self._index.search(q_norm, k)
            return indices, distances

    # ---------- HNSW 搜索 ----------
    def _hnsw_search(self, query: np.ndarray, k: int,
                      ef_search: Optional[int] = None,
                      candidate_mask: Optional[np.ndarray] = None
                      ) -> Tuple[np.ndarray, np.ndarray]:
        """HNSW 搜索（条件过滤时自动增大搜索范围）"""
        if not self._index_built:
            self.build_index()

        if ef_search is not None:
            self._index.set_ef(ef_search)

        if candidate_mask is not None:
            n_candidates = candidate_mask.sum()
            # 增大搜索范围以确保过滤后有足够结果
            search_k = min(max(k * 20, int(n_candidates * 0.2)), self.n_cells)
            indices, distances = self._index.knn_query(query, k=search_k)
            filtered_indices = []
            filtered_distances = []
            for i in range(len(query)):
                valid = candidate_mask[indices[i]]
                fi = indices[i][valid][:k]
                fd = distances[i][valid][:k]
                if len(fi) < k:
                    fi = np.pad(fi, (0, k - len(fi)), constant_values=-1)
                    fd = np.pad(fd, (0, k - len(fd)), constant_values=-1.0)
                filtered_indices.append(fi)
                filtered_distances.append(fd)
            return np.array(filtered_indices), np.array(filtered_distances)
        else:
            indices, distances = self._index.knn_query(query, k=k)
            return indices, distances

    # ===================== 条件过滤 =====================

    def _apply_filters(self, filters: Optional[Dict[str, str]]) -> Optional[np.ndarray]:
        """解析过滤条件，返回布尔 mask"""
        if filters is None or len(filters) == 0:
            return None

        mask = np.ones(self.n_cells, dtype=bool)
        for col, val in filters.items():
            if col not in self.metadata.columns:
                print(f"[SearchEngine] 警告: 过滤列 '{col}' 不存在，已跳过")
                continue
            mask &= (self.metadata[col].astype(str).values == str(val))

        n_match = mask.sum()
        if n_match == 0:
            print(f"[SearchEngine] 警告: 过滤条件 {filters} 无匹配细胞!")

        print(f"[SearchEngine] 过滤条件 {filters}: {n_match}/{self.n_cells} 细胞匹配")
        return mask

    # ===================== 元数据提取 =====================

    def _get_cell_meta(self, cell_idx: int, rank: int, score: float) -> Dict:
        """提取单个细胞的元数据"""
        meta = {
            "rank": rank + 1,
            "cell_index": int(cell_idx),
            "score": float(score),
        }
        for col in self.metadata.columns:
            val = self.metadata.iloc[cell_idx][col]
            if isinstance(val, (np.integer,)):
                val = int(val)
            elif isinstance(val, (np.floating,)):
                val = float(val)
            elif isinstance(val, np.ndarray):
                val = val.tolist()
            else:
                val = str(val)
            meta[col] = val
        return meta

    # ===================== 便捷接口 =====================

    def search_by_cell_index(self,
                              cell_index: int,
                              k: int = 10,
                              filters: Optional[Dict[str, str]] = None,
                              metric: str = "cosine") -> SearchResult:
        """
        以数据集中某个细胞为查询，找最相似的 k 个细胞

        Args:
            cell_index: 细胞在数组中的整数位置 (0-based)
        """
        cell_index = int(cell_index)  # 确保是整数
        query = self.vectors_normalized[cell_index:cell_index+1]
        return self.search(query, k=k, filters=filters, metric=metric)

    def search_by_vector(self,
                          vector: np.ndarray,
                          k: int = 10,
                          filters: Optional[Dict[str, str]] = None,
                          metric: str = "cosine") -> SearchResult:
        """以自定义向量为查询"""
        return self.search(vector, k=k, filters=filters, metric=metric)

    def format_results(self, result: SearchResult, query_idx: int = 0) -> str:
        """格式化输出检索结果"""
        lines = [
            f"\n{'='*70}",
            f"  检索结果 (方法={result.method}, 耗时={result.query_time_ms:.2f}ms)",
            f"{'='*70}",
            f"  {'排名':<6} {'细胞索引':<10} {'相似度/距离':<14} {'细胞类型':<30} {'AgeGroup':<10}",
            f"  {'-'*70}",
        ]
        for meta in result.metadata[query_idx]:
            lines.append(
                f"  {meta['rank']:<6} {meta['cell_index']:<10} "
                f"{meta['score']:<14.6f} {meta.get('cell_type', 'N/A'):<30} "
                f"{meta.get('AgeGroup', 'N/A'):<10}"
            )
        lines.append(f"{'='*70}")
        return "\n".join(lines)

    # ===================== 批量测试 =====================

    def benchmark(self,
                   n_queries: int = 100,
                   k: int = 10,
                   filters: Optional[Dict[str, str]] = None,
                   metric: str = "cosine") -> Dict:
        """性能基准测试"""
        print(f"\n[SearchEngine] ===== 性能基准测试 =====")
        print(f"  方法: {self.method}, 度量: {metric}, k={k}, 查询数: {n_queries}")
        if filters:
            print(f"  过滤条件: {filters}")

        # 随机选择查询细胞
        rng = np.random.RandomState(42)
        if filters:
            mask = self._apply_filters(filters)
            candidates = np.where(mask)[0]
        else:
            candidates = np.arange(self.n_cells)

        query_indices = rng.choice(candidates, size=min(n_queries, len(candidates)),
                                    replace=False)
        queries = self.vectors_normalized[query_indices]

        # 执行检索
        t0 = time.time()
        result = self.search(queries, k=k, filters=filters, metric=metric)
        total_time = (time.time() - t0) * 1000

        stats = {
            "method": result.method,
            "metric": metric,
            "k": k,
            "n_queries": len(query_indices),
            "total_time_ms": total_time,
            "avg_time_ms": total_time / len(query_indices),
            "throughput_qps": len(query_indices) / (total_time / 1000),
            "filters": filters,
        }
        print(f"  总耗时: {total_time:.2f}ms")
        print(f"  平均耗时: {stats['avg_time_ms']:.2f}ms/query")
        print(f"  吞吐量: {stats['throughput_qps']:.1f} queries/s")
        return stats


# ===== 测试入口 =====
if __name__ == "__main__":
    import scanpy as sc

    print("=" * 70)
    print("  单细胞检索系统 - 成员 B")
    print("=" * 70)

    # 1. 加载数据
    adata = sc.read_h5ad("liver.h5ad")
    vectors = adata.obsm["X_pca"][:, :64].astype(np.float32)
    metadata = adata.obs.copy()

    print(f"\n加载: {vectors.shape[0]} 细胞, {vectors.shape[1]} 维 PCA 向量")

    # 2. 测试暴力搜索
    print("\n" + "=" * 70)
    print("  测试 1: 暴力搜索 (余弦相似度)")
    print("=" * 70)
    engine_brute = SearchEngine(vectors, metadata, method="brute")

    # 以第 0 个细胞查询
    result = engine_brute.search_by_cell_index(0, k=10, metric="cosine")
    print(engine_brute.format_results(result))

    # 3. 测试 FAISS
    print("\n" + "=" * 70)
    print("  测试 2: FAISS IVF 搜索")
    print("=" * 70)
    engine_faiss = SearchEngine(vectors, metadata, method="faiss")
    engine_faiss.build_index(nlist=50)
    result2 = engine_faiss.search_by_cell_index(0, k=10, metric="cosine")
    print(engine_faiss.format_results(result2))

    # 4. 测试条件过滤检索
    print("\n" + "=" * 70)
    print("  测试 3: 条件过滤检索 (cell_type='hepatocyte')")
    print("=" * 70)
    result3 = engine_brute.search_by_cell_index(
        0, k=10,
        filters={"cell_type": "hepatocyte"}
    )
    print(engine_brute.format_results(result3))

    # 5. 性能基准
    print("\n" + "=" * 70)
    print("  测试 4: 性能基准")
    print("=" * 70)
    engine_brute.benchmark(n_queries=100, k=10)
    engine_faiss.benchmark(n_queries=100, k=10)

    # 6. 条件过滤 + 性能
    print("\n" + "=" * 70)
    print("  测试 5: 条件过滤检索性能")
    print("=" * 70)
    engine_brute.benchmark(
        n_queries=50, k=10,
        filters={"cell_type": "T cell", "AgeGroup": "Adult"}
    )

    print("\n[SearchEngine] 所有测试完成!")
