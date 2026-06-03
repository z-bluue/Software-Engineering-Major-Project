"""
成员 A 主控脚本
演示完整的索引构建、保存、加载、查询流程
"""

import sys
import json
import numpy as np
from pathlib import Path

# 兼容从成员A目录或项目根目录运行
sys.path.insert(0, str(Path(__file__).parent))
from index_builder import IndexManager, compare_index_methods

# ========================
# 路径配置（根据实际路径修改）
# ========================
VECTORS_PATH = "../成员B文件/data/cell_vectors.npy"   # 成员B提供的向量文件
INDEX_DIR    = "index_store"                      # 索引保存目录


def demo_build_and_save():
    """演示：构建索引并保存到磁盘"""
    print("=" * 65)
    print("  成员 A - 阶段 1: 索引构建 & 保存")
    print("=" * 65)

    mgr = IndexManager(VECTORS_PATH)

    # ---- 构建 FAISS IVF ----
    print("\n>>> 构建 FAISS IVF 索引")
    mgr.build("faiss_ivf", nlist=100, nprobe=10)
    mgr.save(INDEX_DIR)

    # ---- 构建 HNSW（可选，注释掉可跳过）----
    print("\n>>> 构建 HNSW 索引")
    mgr_hnsw = IndexManager(VECTORS_PATH)
    mgr_hnsw.build("hnsw", hnsw_m=16, hnsw_ef_construction=200)
    mgr_hnsw.save(INDEX_DIR + "_hnsw")

    print("\n✓ 索引已保存到:")
    print(f"  FAISS: {INDEX_DIR}/faiss_ivf.index")
    print(f"  HNSW : {INDEX_DIR}_hnsw/hnsw.bin")


def demo_load_and_search():
    """演示：加载索引并执行查询"""
    print("\n" + "=" * 65)
    print("  成员 A - 阶段 2: 加载索引 & 查询")
    print("=" * 65)

    # ---- 加载 FAISS 索引 ----
    print("\n>>> 加载 FAISS 索引")
    mgr = IndexManager(VECTORS_PATH)
    mgr.load(INDEX_DIR)

    # 查询示例 1: 以第 100 个细胞为查询
    query = mgr.vectors_norm[100]
    distances, indices = mgr.search(query, k=10)

    print(f"\n查询细胞 #100 的 Top-10 最相似细胞:")
    print(f"  {'排名':<6} {'细胞索引':<12} {'余弦相似度':<12}")
    print(f"  {'-'*35}")
    for rank, (idx, dist) in enumerate(zip(indices[0], distances[0]), 1):
        print(f"  {rank:<6} {idx:<12} {dist:.6f}")

    # 查询示例 2: 批量查询（前 5 个细胞）
    print(f"\n>>> 批量查询（5条）")
    batch_queries = mgr.vectors_norm[:5]
    batch_distances, batch_indices = mgr.search(batch_queries, k=5)
    for i in range(5):
        print(f"  细胞#{i}: top5索引={batch_indices[i].tolist()}")

    # 状态信息（供成员C的 /api/index/status 接口使用）
    print(f"\n>>> 索引状态")
    print(json.dumps(mgr.status(), ensure_ascii=False, indent=2))

    return mgr


def demo_dynamic_tuning(mgr: IndexManager):
    """演示：动态调整索引参数（精度/速度权衡）"""
    print("\n" + "=" * 65)
    print("  成员 A - 阶段 3: 动态参数调整")
    print("=" * 65)

    import time
    query = mgr.vectors_norm[0]

    for nprobe in [5, 10, 20, 50]:
        mgr.set_nprobe(nprobe)
        t0 = time.time()
        for _ in range(100):
            mgr.search(query, k=10)
        avg_ms = (time.time() - t0) * 1000 / 100
        print(f"  nprobe={nprobe:<4}: 平均查询耗时 {avg_ms:.3f}ms")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "build":
        demo_build_and_save()
    elif mode == "search":
        mgr = demo_load_and_search()
    elif mode == "benchmark":
        compare_index_methods(VECTORS_PATH, n_queries=200, k=10)
    else:
        # 完整演示
        demo_build_and_save()
        mgr = demo_load_and_search()
        demo_dynamic_tuning(mgr)

        print("\n" + "=" * 65)
        print("  成员 A 所有演示完成 ✓")
        print("=" * 65)
