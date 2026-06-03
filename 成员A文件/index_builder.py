"""
索引构建模块 (成员 A)
- 读取成员 B 导出的 PCA 向量 (cell_vectors.npy)
- 支持 FAISS IVF / HNSW 两种 ANN 索引
- 索引的构建、保存、加载
- 多数据集联合索引与动态管理（结项功能）
- 对外提供统一的 IndexManager 接口供成员 C 后端集成
"""

import os
import time
import json
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Tuple, List
import warnings
warnings.filterwarnings("ignore")


# ===================== 数据类 =====================

class IndexInfo:
    """索引元信息"""

    def __init__(self, method: str, n_cells: int, n_dims: int,
                 build_time_s: float, params: Dict):
        self.method = method
        self.n_cells = n_cells
        self.n_dims = n_dims
        self.build_time_s = build_time_s
        self.params = params

    def to_dict(self) -> Dict:
        return {
            "method": self.method,
            "n_cells": self.n_cells,
            "n_dims": self.n_dims,
            "build_time_s": round(self.build_time_s, 3),
            "params": self.params,
        }

    def __repr__(self):
        return (f"IndexInfo(method={self.method}, n_cells={self.n_cells}, "
                f"n_dims={self.n_dims}, build_time={self.build_time_s:.2f}s)")


# ===================== 核心：IndexManager =====================

class IndexManager:
    """
    ANN 索引管理器 (成员 A 核心模块)

    功能:
      - 从 .npy 文件加载向量
      - 构建 FAISS IVF 或 HNSW 索引
      - 索引持久化 (保存 / 加载)
      - 多数据集联合索引与动态管理（新增/删除数据集）
      - 查询接口 (供成员 C 后端直接调用)

    快速上手:
        mgr = IndexManager("cell_vectors.npy")
        mgr.build("faiss_ivf")
        mgr.save("index_store/")
        mgr.load("index_store/", "faiss_ivf")
        D, I = mgr.search(query, k=10)
    """

    def __init__(self, vectors_path: str = "cell_vectors.npy"):
        self.vectors_path = Path(vectors_path)
        self.vectors: Optional[np.ndarray] = None
        self.vectors_norm: Optional[np.ndarray] = None
        self.n_cells: int = 0
        self.n_dims: int = 0

        # 多数据集管理
        # dataset_registry: {dataset_id: {"name": str, "start": int, "end": int, "n_cells": int}}
        self.dataset_registry: Dict[str, Dict] = {}

        # 索引对象
        self._faiss_index = None
        self._hnsw_index = None
        self._active_method: Optional[str] = None

        # 元信息
        self.index_info: Optional[IndexInfo] = None

        # 自动加载向量
        self._load_vectors()

    # -------------------- 向量加载 --------------------

    def _load_vectors(self) -> None:
        """加载成员 B 导出的 PCA 向量"""
        if not self.vectors_path.exists():
            raise FileNotFoundError(
                f"向量文件不存在: {self.vectors_path}\n"
                f"请确认成员 B 的 cell_vectors.npy 已放置到正确路径"
            )

        print(f"[IndexManager] 加载向量: {self.vectors_path}")
        self.vectors = np.load(str(self.vectors_path)).astype(np.float32)
        self.n_cells, self.n_dims = self.vectors.shape
        print(f"[IndexManager] 向量 shape: {self.vectors.shape}, dtype={self.vectors.dtype}")

        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.vectors_norm = self.vectors / norms
        print(f"[IndexManager] L2 归一化完成，余弦相似度 = 内积")

        # 默认将初始数据集注册为 "default"
        if not self.dataset_registry:
            self.dataset_registry["default"] = {
                "name": "default",
                "path": str(self.vectors_path),
                "start": 0,
                "end": self.n_cells,
                "n_cells": self.n_cells,
            }

    # -------------------- 索引构建 --------------------

    def build(self,
              method: str = "faiss_ivf",
              nlist: int = 100,
              nprobe: int = 10,
              hnsw_m: int = 16,
              hnsw_ef_construction: int = 200) -> IndexInfo:
        """
        构建 ANN 索引

        Args:
            method: "faiss_ivf" 或 "hnsw"
            nlist: [FAISS] 聚类中心数
            nprobe: [FAISS] 搜索时探测的聚类数
            hnsw_m: [HNSW] 每层最大连接数
            hnsw_ef_construction: [HNSW] 构建时搜索宽度
        """
        print(f"\n[IndexManager] ===== 构建索引: {method} =====")

        if method == "faiss_ivf":
            info = self._build_faiss_ivf(nlist, nprobe)
        elif method == "hnsw":
            info = self._build_hnsw(hnsw_m, hnsw_ef_construction)
        else:
            raise ValueError(f"不支持的索引方法: {method}，请选择 'faiss_ivf' 或 'hnsw'")

        self._active_method = method
        self.index_info = info
        print(f"[IndexManager] 索引构建完成: {info}")
        return info

    def _build_faiss_ivf(self, nlist: int, nprobe: int) -> IndexInfo:
        """构建 FAISS IVF 索引"""
        try:
            import faiss
        except ImportError:
            raise ImportError("FAISS 未安装！请运行: pip install faiss-cpu")

        print(f"[IndexManager] FAISS IVF: nlist={nlist}, nprobe={nprobe}")
        print(f"[IndexManager] 向量数={self.n_cells}, 维度={self.n_dims}")

        t0 = time.time()
        quantizer = faiss.IndexFlatIP(self.n_dims)
        index = faiss.IndexIVFFlat(quantizer, self.n_dims, nlist,
                                    faiss.METRIC_INNER_PRODUCT)

        print(f"[IndexManager] 训练聚类中心（nlist={nlist}）...")
        index.train(self.vectors_norm)
        print(f"[IndexManager] 添加 {self.n_cells} 个向量...")
        index.add(self.vectors_norm)
        index.nprobe = nprobe
        self._faiss_index = index

        elapsed = time.time() - t0
        print(f"[IndexManager] FAISS IVF 构建完成，耗时 {elapsed:.2f}s")
        print(f"[IndexManager] 索引向量数: {index.ntotal}")

        return IndexInfo("faiss_ivf", self.n_cells, self.n_dims, elapsed,
                         {"nlist": nlist, "nprobe": nprobe})

    def _build_hnsw(self, M: int, ef_construction: int) -> IndexInfo:
        """构建 HNSW 索引"""
        try:
            import hnswlib
        except ImportError:
            raise ImportError("hnswlib 未安装！请运行: pip install hnswlib")

        print(f"[IndexManager] HNSW: M={M}, ef_construction={ef_construction}")

        t0 = time.time()
        index = hnswlib.Index(space="cosine", dim=self.n_dims)
        index.init_index(max_elements=self.n_cells,
                         ef_construction=ef_construction, M=M)

        print(f"[IndexManager] 添加 {self.n_cells} 个向量到 HNSW...")
        index.add_items(self.vectors, np.arange(self.n_cells))
        default_ef = min(ef_construction, 100)
        index.set_ef(default_ef)
        self._hnsw_index = index

        elapsed = time.time() - t0
        print(f"[IndexManager] HNSW 构建完成，耗时 {elapsed:.2f}s")

        return IndexInfo("hnsw", self.n_cells, self.n_dims, elapsed,
                         {"M": M, "ef_construction": ef_construction,
                          "ef_search": default_ef})

    # -------------------- 索引持久化 --------------------

    def save(self, save_dir: str = "index_store") -> None:
        """保存索引到磁盘"""
        if self._active_method is None:
            raise RuntimeError("请先调用 build() 构建索引")

        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        print(f"\n[IndexManager] 保存索引到: {save_path.resolve()}")

        if self._active_method == "faiss_ivf" and self._faiss_index is not None:
            import faiss
            idx_path = save_path / "faiss_ivf.index"
            faiss.write_index(self._faiss_index, str(idx_path))
            print(f"[IndexManager] FAISS 索引已保存: {idx_path}")

        if self._active_method == "hnsw" and self._hnsw_index is not None:
            idx_path = save_path / "hnsw.bin"
            self._hnsw_index.save_index(str(idx_path))
            print(f"[IndexManager] HNSW 索引已保存: {idx_path}")

        # 保存元信息（含数据集注册表）
        meta = {
            "active_method": self._active_method,
            "n_cells": self.n_cells,
            "n_dims": self.n_dims,
            "vectors_path": str(self.vectors_path),
            "dataset_registry": self.dataset_registry,
        }
        if self.index_info:
            meta["index_info"] = self.index_info.to_dict()

        meta_path = save_path / "index_meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"[IndexManager] 元信息已保存: {meta_path}")

    def load(self, save_dir: str = "index_store",
             method: Optional[str] = None) -> None:
        """从磁盘加载已保存的索引"""
        save_path = Path(save_dir)
        meta_path = save_path / "index_meta.json"

        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if method is None:
                method = meta.get("active_method")
            # 恢复数据集注册表
            if "dataset_registry" in meta:
                self.dataset_registry = meta["dataset_registry"]
            print(f"[IndexManager] 读取元信息: {meta_path}")
        else:
            if method is None:
                raise FileNotFoundError("找不到 index_meta.json，请手动指定 method 参数")

        print(f"\n[IndexManager] ===== 加载索引: {method} =====")
        t0 = time.time()

        if method == "faiss_ivf":
            import faiss
            idx_path = save_path / "faiss_ivf.index"
            if not idx_path.exists():
                raise FileNotFoundError(f"FAISS 索引文件不存在: {idx_path}")
            self._faiss_index = faiss.read_index(str(idx_path))
            print(f"[IndexManager] FAISS 索引加载完成，向量数: {self._faiss_index.ntotal}")

        elif method == "hnsw":
            import hnswlib
            idx_path = save_path / "hnsw.bin"
            if not idx_path.exists():
                raise FileNotFoundError(f"HNSW 索引文件不存在: {idx_path}")
            index = hnswlib.Index(space="cosine", dim=self.n_dims)
            index.load_index(str(idx_path), max_elements=self.n_cells)
            self._hnsw_index = index
            print(f"[IndexManager] HNSW 索引加载完成")
        else:
            raise ValueError(f"不支持的索引方法: {method}")

        self._active_method = method
        print(f"[IndexManager] 加载耗时: {time.time()-t0:.2f}s")

    # ==================== 多数据集联合索引 ====================

    def add_dataset(self, dataset_id: str, vectors_path: str,
                    rebuild: bool = True) -> Dict:
        """
        添加新数据集到联合索引（动态管理）

        原理：将新数据集的向量追加到现有向量后，重建索引。
        FAISS IVF 支持增量 add()，HNSW 需要扩容后重新 add。

        Args:
            dataset_id: 数据集唯一标识，如 "dataset_kidney"
            vectors_path: 新数据集的 .npy 向量文件路径
            rebuild: 是否在添加后立即重建索引（默认 True）

        Returns:
            添加后的数据集注册信息
        """
        if dataset_id in self.dataset_registry:
            raise ValueError(f"数据集 '{dataset_id}' 已存在，请先调用 remove_dataset() 删除后再添加")

        new_path = Path(vectors_path)
        if not new_path.exists():
            raise FileNotFoundError(f"向量文件不存在: {new_path}")

        print(f"\n[IndexManager] ===== 添加数据集: {dataset_id} =====")
        new_vectors = np.load(str(new_path)).astype(np.float32)

        if new_vectors.shape[1] != self.n_dims:
            raise ValueError(
                f"维度不匹配：现有索引维度={self.n_dims}，"
                f"新数据集维度={new_vectors.shape[1]}"
            )

        # L2 归一化
        norms = np.linalg.norm(new_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        new_vectors_norm = new_vectors / norms

        # 记录偏移量
        start_idx = self.n_cells
        end_idx = self.n_cells + len(new_vectors)

        # 追加向量
        self.vectors = np.vstack([self.vectors, new_vectors])
        self.vectors_norm = np.vstack([self.vectors_norm, new_vectors_norm])
        self.n_cells = end_idx

        # 注册数据集
        info = {
            "name": dataset_id,
            "path": str(new_path),
            "start": start_idx,
            "end": end_idx,
            "n_cells": len(new_vectors),
        }
        self.dataset_registry[dataset_id] = info
        print(f"[IndexManager] 数据集 '{dataset_id}' 追加完成: "
              f"{len(new_vectors)} 个细胞，索引范围 [{start_idx}, {end_idx})")
        print(f"[IndexManager] 当前总细胞数: {self.n_cells}")

        # 重建索引
        if rebuild and self._active_method is not None:
            print(f"[IndexManager] 重建 {self._active_method} 索引...")
            self.build(self._active_method)

        return info

    def remove_dataset(self, dataset_id: str, rebuild: bool = True) -> None:
        """
        从联合索引中删除数据集（动态管理）

        原理：删除对应索引段的向量，更新所有后续数据集的偏移量，重建索引。

        Args:
            dataset_id: 要删除的数据集 ID
            rebuild: 是否在删除后立即重建索引
        """
        if dataset_id not in self.dataset_registry:
            raise KeyError(f"数据集 '{dataset_id}' 不存在")

        print(f"\n[IndexManager] ===== 删除数据集: {dataset_id} =====")
        info = self.dataset_registry[dataset_id]
        start, end = info["start"], info["end"]
        removed_count = end - start

        # 从向量矩阵中删除对应行
        keep_mask = np.ones(self.n_cells, dtype=bool)
        keep_mask[start:end] = False
        self.vectors = self.vectors[keep_mask]
        self.vectors_norm = self.vectors_norm[keep_mask]
        self.n_cells = len(self.vectors)

        # 更新后续数据集的偏移量
        del self.dataset_registry[dataset_id]
        for did, dinfo in self.dataset_registry.items():
            if dinfo["start"] >= end:
                dinfo["start"] -= removed_count
                dinfo["end"] -= removed_count

        print(f"[IndexManager] 数据集 '{dataset_id}' 已删除（{removed_count} 个细胞）")
        print(f"[IndexManager] 当前总细胞数: {self.n_cells}")

        if rebuild and self._active_method is not None and self.n_cells > 0:
            print(f"[IndexManager] 重建 {self._active_method} 索引...")
            self.build(self._active_method)

    def get_dataset_of_cell(self, cell_index: int) -> Optional[str]:
        """
        根据细胞索引查询其所属数据集 ID

        Args:
            cell_index: 细胞在全局向量矩阵中的 0-based 索引

        Returns:
            所属数据集 ID，若未找到返回 None
        """
        for did, info in self.dataset_registry.items():
            if info["start"] <= cell_index < info["end"]:
                return did
        return None

    def list_datasets(self) -> List[Dict]:
        """列出所有已注册的数据集信息"""
        result = []
        for did, info in self.dataset_registry.items():
            result.append({
                "dataset_id": did,
                "name": info.get("name", did),
                "n_cells": info["n_cells"],
                "index_range": [info["start"], info["end"]],
                "path": info.get("path", ""),
            })
        return result

    # -------------------- 查询接口 --------------------

    def search(self,
               query: np.ndarray,
               k: int = 10,
               ef_search: Optional[int] = None,
               dataset_filter: Optional[str] = None
               ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Top-K 近似最近邻检索（供成员 C 后端直接调用）

        Args:
            query: 查询向量，shape (n_dims,) 或 (n_queries, n_dims)
            k: 返回 top-k 个最相似细胞
            ef_search: [HNSW] 查询精度
            dataset_filter: 限制只在指定数据集内检索（如 "dataset_kidney"）

        Returns:
            distances: shape (n_queries, k)，余弦相似度（越大越相似）
            indices:   shape (n_queries, k)，细胞索引（0-based，全局索引）
        """
        if self._active_method is None:
            raise RuntimeError("索引未就绪，请先调用 build() 或 load()")

        if query.ndim == 1:
            query = query.reshape(1, -1)
        query = query.astype(np.float32)
        q_norm = query / (np.linalg.norm(query, axis=1, keepdims=True) + 1e-10)

        # 数据集过滤：只在指定数据集范围内检索
        if dataset_filter is not None:
            return self._search_with_dataset_filter(q_norm, k, dataset_filter)

        if self._active_method == "faiss_ivf":
            return self._search_faiss(q_norm, k)
        elif self._active_method == "hnsw":
            return self._search_hnsw(q_norm, k, ef_search)
        else:
            raise RuntimeError(f"未知方法: {self._active_method}")

    def _search_faiss(self, q_norm: np.ndarray, k: int
                      ) -> Tuple[np.ndarray, np.ndarray]:
        distances, indices = self._faiss_index.search(q_norm, k)
        return distances, indices

    def _search_hnsw(self, q_norm: np.ndarray, k: int,
                     ef_search: Optional[int]) -> Tuple[np.ndarray, np.ndarray]:
        if ef_search is not None:
            self._hnsw_index.set_ef(ef_search)
        labels, distances = self._hnsw_index.knn_query(q_norm, k=k)
        similarities = 1.0 - distances
        return similarities.astype(np.float32), labels.astype(np.int64)

    def _search_with_dataset_filter(self, q_norm: np.ndarray, k: int,
                                     dataset_id: str
                                     ) -> Tuple[np.ndarray, np.ndarray]:
        """在指定数据集范围内做暴力检索（数据集过滤时用）"""
        if dataset_id not in self.dataset_registry:
            raise KeyError(f"数据集 '{dataset_id}' 不存在")

        info = self.dataset_registry[dataset_id]
        start, end = info["start"], info["end"]
        subset_norm = self.vectors_norm[start:end]

        # 暴力余弦相似度
        sim = np.dot(q_norm, subset_norm.T)  # (n_queries, subset_size)
        top_k = min(k, sim.shape[1])
        local_indices = np.argsort(-sim, axis=1)[:, :top_k]
        top_distances = np.take_along_axis(sim, local_indices, axis=1)

        # 转为全局索引
        global_indices = local_indices + start
        return top_distances.astype(np.float32), global_indices.astype(np.int64)

    # -------------------- 状态查询 --------------------

    def status(self) -> Dict:
        """返回当前索引状态，供成员 C 的 /api/index/status 接口使用"""
        return {
            "active_method": self._active_method,
            "n_cells": self.n_cells,
            "n_dims": self.n_dims,
            "faiss_ready": self._faiss_index is not None,
            "hnsw_ready": self._hnsw_index is not None,
            "n_datasets": len(self.dataset_registry),
            "datasets": self.list_datasets(),
            "index_info": self.index_info.to_dict() if self.index_info else None,
        }

    def set_nprobe(self, nprobe: int) -> None:
        """动态调整 FAISS 的 nprobe（精度/速度权衡）"""
        if self._faiss_index is not None:
            self._faiss_index.nprobe = nprobe
            print(f"[IndexManager] FAISS nprobe 已更新为 {nprobe}")
        else:
            print("[IndexManager] 警告: FAISS 索引未构建")

    def set_ef_search(self, ef: int) -> None:
        """动态调整 HNSW 的 ef_search（精度/速度权衡）"""
        if self._hnsw_index is not None:
            self._hnsw_index.set_ef(ef)
            print(f"[IndexManager] HNSW ef_search 已更新为 {ef}")
        else:
            print("[IndexManager] 警告: HNSW 索引未构建")


# ===================== 性能对比工具 =====================

def compare_index_methods(vectors_path: str = "cell_vectors.npy",
                           n_queries: int = 200,
                           k: int = 10) -> Dict:
    """
    对比 FAISS IVF 与 HNSW 的构建时间、查询速度和召回率

    Returns:
        Dict: 包含两种方法的性能统计
    """
    print("\n" + "=" * 70)
    print("  索引方法性能对比: FAISS IVF vs HNSW")
    print("=" * 70)

    mgr = IndexManager(vectors_path)
    vectors = mgr.vectors_norm

    rng = np.random.RandomState(42)
    query_idx = rng.choice(mgr.n_cells, size=min(n_queries, mgr.n_cells), replace=False)
    queries = vectors[query_idx]

    results = {}

    # ---------- FAISS IVF ----------
    print("\n--- FAISS IVF ---")
    mgr_f = IndexManager(vectors_path)
    info_f = mgr_f.build("faiss_ivf", nlist=100, nprobe=10)
    t0 = time.time()
    for q in queries:
        mgr_f.search(q, k=k)
    faiss_query_ms = (time.time() - t0) * 1000 / len(queries)

    # ---------- HNSW ----------
    print("\n--- HNSW ---")
    mgr_h = IndexManager(vectors_path)
    info_h = mgr_h.build("hnsw", hnsw_m=16, hnsw_ef_construction=200)
    t0 = time.time()
    for q in queries:
        mgr_h.search(q, k=k)
    hnsw_query_ms = (time.time() - t0) * 1000 / len(queries)

    # ---------- 召回率（以暴力搜索为 ground truth）----------
    print("\n--- 计算召回率 ---")
    gt_indices = _brute_search(vectors, queries, k)
    faiss_indices = np.vstack([mgr_f.search(q, k=k)[1] for q in queries])
    hnsw_indices = np.vstack([mgr_h.search(q, k=k)[1].flatten() for q in queries])

    recall_faiss = _calc_recall(gt_indices, faiss_indices, k)
    recall_hnsw = _calc_recall(gt_indices, hnsw_indices, k)

    results = {
        "faiss_ivf": {
            "build_time_s": info_f.build_time_s,
            "avg_query_ms": faiss_query_ms,
            "recall_at_k": recall_faiss,
            "params": info_f.params,
        },
        "hnsw": {
            "build_time_s": info_h.build_time_s,
            "avg_query_ms": hnsw_query_ms,
            "recall_at_k": recall_hnsw,
            "params": info_h.params,
        }
    }

    print("\n" + "=" * 70)
    print(f"  {'方法':<15} {'构建耗时(s)':<15} {'查询耗时(ms)':<16} {'召回率@' + str(k):<12}")
    print(f"  {'-'*60}")
    for m, r in results.items():
        print(f"  {m:<15} {r['build_time_s']:<15.2f} "
              f"{r['avg_query_ms']:<16.3f} {r['recall_at_k']:.2%}")
    print("=" * 70)

    return results


def _brute_search(vectors_norm: np.ndarray,
                  queries: np.ndarray, k: int) -> np.ndarray:
    """暴力搜索（召回率 ground truth）"""
    q_norm = queries / (np.linalg.norm(queries, axis=1, keepdims=True) + 1e-10)
    sim = np.dot(q_norm, vectors_norm.T)
    return np.argsort(-sim, axis=1)[:, :k]


def _calc_recall(gt: np.ndarray, pred: np.ndarray, k: int) -> float:
    """计算 Recall@K"""
    recalls = []
    for i in range(len(gt)):
        gt_set = set(gt[i].tolist())
        pred_set = set(pred[i].tolist())
        pred_set.discard(-1)
        if len(gt_set) > 0:
            recalls.append(len(gt_set & pred_set) / len(gt_set))
    return float(np.mean(recalls)) if recalls else 0.0


# ===================== 测试入口 =====================

if __name__ == "__main__":
    import sys

    VECTORS_PATH = "cell_vectors.npy"
    INDEX_DIR = "index_store"

    print("=" * 70)
    print("  成员 A - ANN 索引构建模块测试")
    print("=" * 70)

    if not Path(VECTORS_PATH).exists():
        alt_path = "../成员B文件/data/cell_vectors.npy"
        if Path(alt_path).exists():
            VECTORS_PATH = alt_path
            print(f"[提示] 使用成员B目录的向量: {VECTORS_PATH}")
        else:
            print(f"[错误] 找不到向量文件: {VECTORS_PATH}")
            sys.exit(1)

    # -------- 测试 1: 构建 FAISS 索引并保存 --------
    print("\n--- 测试 1: 构建 FAISS IVF 索引 ---")
    mgr = IndexManager(VECTORS_PATH)
    mgr.build("faiss_ivf", nlist=100, nprobe=10)
    mgr.save(INDEX_DIR)

    # -------- 测试 2: 从磁盘加载索引 --------
    print("\n--- 测试 2: 从磁盘加载 FAISS 索引 ---")
    mgr2 = IndexManager(VECTORS_PATH)
    mgr2.load(INDEX_DIR)

    # -------- 测试 3: 查询 --------
    print("\n--- 测试 3: 查询（以第 0 个细胞为查询）---")
    query = mgr2.vectors_norm[0]
    distances, indices = mgr2.search(query, k=10)
    print(f"  Top-10 索引: {indices[0].tolist()}")
    print(f"  Top-10 相似度: {[f'{d:.4f}' for d in distances[0].tolist()]}")
    assert distances[0][0] >= 0.9999, "Top-1 相似度应接近 1.0"
    print("  ✓ 相似度验证通过")

    # -------- 测试 4: 构建 HNSW 索引 --------
    print("\n--- 测试 4: 构建 HNSW 索引 ---")
    mgr3 = IndexManager(VECTORS_PATH)
    mgr3.build("hnsw", hnsw_m=16, hnsw_ef_construction=200)
    mgr3.save(INDEX_DIR + "_hnsw")

    # -------- 测试 5: 多数据集 - 添加数据集 --------
    print("\n--- 测试 5: 多数据集联合索引 ---")
    mgr4 = IndexManager(VECTORS_PATH)
    mgr4.build("faiss_ivf", nlist=100, nprobe=10)
    print(f"  添加前数据集列表: {mgr4.list_datasets()}")

    # 用同一份向量模拟第二个数据集（实际中会是另一个 .npy 文件）
    new_vectors_path = VECTORS_PATH
    mgr4.add_dataset("dataset_extra", new_vectors_path, rebuild=True)
    print(f"  添加后总细胞数: {mgr4.n_cells}")
    print(f"  数据集列表: {[d['dataset_id'] for d in mgr4.list_datasets()]}")

    # 按数据集过滤检索
    q = mgr4.vectors_norm[0]
    dist_filtered, idx_filtered = mgr4.search(q, k=5, dataset_filter="default")
    print(f"  仅在 'default' 数据集内检索 Top-5: {idx_filtered[0].tolist()}")

    # -------- 测试 6: 删除数据集 --------
    print("\n--- 测试 6: 删除数据集 ---")
    mgr4.remove_dataset("dataset_extra", rebuild=True)
    print(f"  删除后总细胞数: {mgr4.n_cells}")
    print(f"  数据集列表: {[d['dataset_id'] for d in mgr4.list_datasets()]}")

    # -------- 测试 7: 索引状态 --------
    print("\n--- 测试 7: 索引状态 ---")
    status = mgr2.status()
    print(f"  状态: {json.dumps(status, ensure_ascii=False, indent=2)}")

    # -------- 测试 8: 性能对比（可选）--------
    if "--benchmark" in sys.argv:
        print("\n--- 测试 8: FAISS vs HNSW 性能对比 ---")
        compare_index_methods(VECTORS_PATH, n_queries=200, k=10)

    print("\n[成员 A] 所有测试完成 ✓")
