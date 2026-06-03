"""
性能评测脚本 (成员 A)
- FAISS IVF vs HNSW vs 暴力搜索 三方对比
- 输出构建耗时、查询耗时、Recall@K、吞吐量
- 测试数据: 成员B导出的 cell_vectors.npy (69032 × 30, float32)
"""

import time
import json
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from index_builder import IndexManager, _brute_search, _calc_recall

VECTORS_PATH = "../成员B文件/data/cell_vectors.npy"
if not Path(VECTORS_PATH).exists():
    VECTORS_PATH = "cell_vectors.npy"

N_QUERIES   = 200   # 评测查询数
K           = 10    # Top-K


def benchmark_build_time() -> dict:
    """测试三种方法的索引构建耗时"""
    print("\n" + "=" * 65)
    print("  阶段 1 / 3 — 索引构建耗时")
    print("=" * 65)

    results = {}

    # FAISS IVF
    mgr = IndexManager(VECTORS_PATH)
    t0 = time.time()
    mgr.build("faiss_ivf", nlist=100, nprobe=10)
    results["faiss_ivf"] = {"build_time_s": round(time.time() - t0, 3)}
    print(f"  FAISS IVF  构建耗时: {results['faiss_ivf']['build_time_s']:.3f}s")

    # HNSW
    mgr2 = IndexManager(VECTORS_PATH)
    t0 = time.time()
    mgr2.build("hnsw", hnsw_m=16, hnsw_ef_construction=200)
    results["hnsw"] = {"build_time_s": round(time.time() - t0, 3)}
    print(f"  HNSW       构建耗时: {results['hnsw']['build_time_s']:.3f}s")

    # 暴力搜索（无需构建）
    results["brute"] = {"build_time_s": 0.0}
    print(f"  暴力搜索   构建耗时: 0.000s（无需构建）")

    return results, mgr, mgr2


def benchmark_query_speed(mgr_faiss, mgr_hnsw, queries) -> dict:
    """测试三种方法的单次查询平均耗时与吞吐量"""
    print("\n" + "=" * 65)
    print("  阶段 2 / 3 — 查询速度 & 吞吐量")
    print("=" * 65)

    results = {}
    vectors_norm = mgr_faiss.vectors_norm

    # FAISS IVF
    t0 = time.time()
    for q in queries:
        mgr_faiss.search(q, k=K)
    elapsed_ms = (time.time() - t0) * 1000
    results["faiss_ivf"] = {
        "avg_query_ms": round(elapsed_ms / len(queries), 3),
        "throughput_qps": round(len(queries) / (elapsed_ms / 1000), 1),
    }
    print(f"  FAISS IVF  平均查询: {results['faiss_ivf']['avg_query_ms']:.3f}ms  "
          f"吞吐: {results['faiss_ivf']['throughput_qps']:.0f} qps")

    # HNSW
    t0 = time.time()
    for q in queries:
        mgr_hnsw.search(q, k=K)
    elapsed_ms = (time.time() - t0) * 1000
    results["hnsw"] = {
        "avg_query_ms": round(elapsed_ms / len(queries), 3),
        "throughput_qps": round(len(queries) / (elapsed_ms / 1000), 1),
    }
    print(f"  HNSW       平均查询: {results['hnsw']['avg_query_ms']:.3f}ms  "
          f"吞吐: {results['hnsw']['throughput_qps']:.0f} qps")

    # 暴力搜索
    t0 = time.time()
    for q in queries:
        q2 = q.reshape(1, -1)
        sim = np.dot(q2, vectors_norm.T)
        np.argsort(-sim, axis=1)[:, :K]
    elapsed_ms = (time.time() - t0) * 1000
    results["brute"] = {
        "avg_query_ms": round(elapsed_ms / len(queries), 3),
        "throughput_qps": round(len(queries) / (elapsed_ms / 1000), 1),
    }
    print(f"  暴力搜索   平均查询: {results['brute']['avg_query_ms']:.3f}ms  "
          f"吞吐: {results['brute']['throughput_qps']:.0f} qps")

    return results


def benchmark_recall(mgr_faiss, mgr_hnsw, queries, gt_indices) -> dict:
    """计算 FAISS 和 HNSW 相对于暴力搜索的 Recall@K"""
    print("\n" + "=" * 65)
    print(f"  阶段 3 / 3 — 召回率 Recall@{K}")
    print("=" * 65)

    faiss_indices = np.vstack([mgr_faiss.search(q, k=K)[1] for q in queries])
    hnsw_indices  = np.vstack([mgr_hnsw.search(q,  k=K)[1].flatten() for q in queries])

    recall_faiss = _calc_recall(gt_indices, faiss_indices, K)
    recall_hnsw  = _calc_recall(gt_indices, hnsw_indices,  K)

    print(f"  FAISS IVF  Recall@{K}: {recall_faiss:.2%}")
    print(f"  HNSW       Recall@{K}: {recall_hnsw:.2%}")
    print(f"  暴力搜索   Recall@{K}: 100.00%（基准）")

    return {
        "faiss_ivf": {"recall_at_k": round(recall_faiss, 4)},
        "hnsw":      {"recall_at_k": round(recall_hnsw,  4)},
        "brute":     {"recall_at_k": 1.0},
    }


def main():
    print("=" * 65)
    print("  成员 A — ANN 索引性能评测")
    print(f"  数据: {Path(VECTORS_PATH).name}  "
          f"| 查询数: {N_QUERIES}  | Top-K: {K}")
    print("=" * 65)

    # 准备查询集
    tmp = IndexManager(VECTORS_PATH)
    rng = np.random.RandomState(42)
    q_idx = rng.choice(tmp.n_cells, size=min(N_QUERIES, tmp.n_cells), replace=False)
    queries = tmp.vectors_norm[q_idx]
    gt_indices = _brute_search(tmp.vectors_norm, queries, K)
    del tmp

    # 三阶段评测
    build_results, mgr_faiss, mgr_hnsw = benchmark_build_time()
    speed_results = benchmark_query_speed(mgr_faiss, mgr_hnsw, queries)
    recall_results = benchmark_recall(mgr_faiss, mgr_hnsw, queries, gt_indices)

    # 合并结果
    final = {}
    for method in ["faiss_ivf", "hnsw", "brute"]:
        final[method] = {
            **build_results.get(method, {}),
            **speed_results.get(method, {}),
            **recall_results.get(method, {}),
        }

    # 打印汇总表
    print("\n" + "=" * 75)
    print("  性能评测汇总表（数据集: liver.h5ad | 69,032 细胞 | 30 维 PCA）")
    print("=" * 75)
    header = f"  {'方法':<14} {'构建耗时(s)':<14} {'查询耗时(ms)':<15} {'吞吐(qps)':<12} {'召回率@' + str(K):<10}"
    print(header)
    print("  " + "-" * 65)
    display_names = {"faiss_ivf": "FAISS IVF", "hnsw": "HNSW", "brute": "暴力搜索"}
    for method, name in display_names.items():
        r = final[method]
        print(f"  {name:<14} "
              f"{r.get('build_time_s', 0):<14.3f} "
              f"{r.get('avg_query_ms', 0):<15.3f} "
              f"{r.get('throughput_qps', 0):<12.0f} "
              f"{r.get('recall_at_k', 0):.2%}")
    print("=" * 75)

    # 保存 JSON
    out_path = Path(__file__).parent / "benchmark_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print(f"\n  评测结果已保存: {out_path}")

    return final


if __name__ == "__main__":
    main()
