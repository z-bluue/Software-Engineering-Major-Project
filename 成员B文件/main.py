"""
主控整合脚本 (成员 B)
- 完整流水线: 数据读取 → 预处理 → 降维 → 索引构建 → 检索
- 导出接口供成员 A/C/D/E 使用
- 演示 & 测试
"""

import sys
import time
import numpy as np
import scanpy as sc
from pathlib import Path

from data_manager import DataManager
from preprocessing import Preprocessor
from search_engine import SearchEngine


def demo_pipeline():
    """演示完整流水线"""
    print("=" * 75)
    print("  成员 B - 单细胞数据处理与检索系统")
    print("=" * 75)

    # ======== 阶段 1: 数据管理 ========
    print("\n" + "=" * 75)
    print("  阶段 1: 数据管理")
    print("=" * 75)

    dm = DataManager("liver.h5ad")
    dm.load_data()
    dm.validate_data()
    summary = dm.summary()
    print(f"\n数据摘要:")
    print(f"  细胞数: {summary['n_cells']}")
    print(f"  基因数: {summary['n_genes']}")
    print(f"  细胞类型: {len(summary['cell_types'])} 种")
    print(f"  已有 PCA: {summary['pca_dims']}")
    print(f"  已有 UMAP: {summary['umap_dims']}")

    # ======== 阶段 2: 数据预处理 ========
    print("\n" + "=" * 75)
    print("  阶段 2: 数据预处理 (QC → 标准化 → HVG → 缩放 → PCA)")
    print("=" * 75)

    preprocessor = Preprocessor(dm.adata)
    adata_processed, pca_vectors_new = preprocessor.run_full_pipeline(
        n_top_genes=2000,
        n_pca_comps=64,
        hv_flavor="seurat"
    )

    # 也可使用数据中自带的 PCA
    pca_vectors_existing = dm.get_pca_vectors(n_dims=64)
    print(f"\n自带 PCA 向量: {pca_vectors_existing.shape}")
    print(f"新算 PCA 向量: {pca_vectors_new.shape}")

    # 使用自带 PCA (更快速)
    use_vectors = pca_vectors_existing

    # ======== 阶段 3: 导出向量给成员 A ========
    print("\n" + "=" * 75)
    print("  阶段 3: 导出接口")
    print("=" * 75)

    # 3a. 给成员 A: PCA 向量 (.npy)
    dm.export_vectors_for_index("output/cell_vectors.npy", n_dims=64)

    # 3b. 给成员 C: 元数据 (CSV)
    dm.export_metadata("output/cell_metadata.csv")

    # 3c. 给成员 D: 2D 坐标 (CSV)
    dm.export_2d_coords("umap", "output/cell_2d_coords.csv")

    # 3d. 给成员 E: 全量向量 + 元数据 (用于 ground truth)
    np.save("output/full_vectors.npy", use_vectors)
    dm.adata.obs.to_csv("output/full_metadata.csv")

    print("\n[导出] 所有文件已输出到 output/ 目录")

    # ======== 阶段 4: 检索系统演示 ========
    print("\n" + "=" * 75)
    print("  阶段 4: Top-K 相似细胞检索")
    print("=" * 75)

    metadata = dm.adata.obs.copy()
    engine = SearchEngine(use_vectors, metadata, method="faiss")
    engine.build_index(nlist=100, nprobe=10)

    # 演示 1: 基础 Top-K 检索
    print("\n--- 演示 1: 基础 Top-10 检索 (以第0个细胞为查询) ---")
    query_idx = 0
    query_type = metadata.iloc[query_idx]["cell_type"]
    print(f"  查询细胞: index={query_idx}, cell_type={query_type}")
    result1 = engine.search_by_cell_index(query_idx, k=10)
    print(engine.format_results(result1))

    # 演示 2: 条件过滤检索 (仅搜索 T cell + Adult)
    print("\n--- 演示 2: 条件过滤检索 (仅搜索 T cell + Adult) ---")
    result2 = engine.search_by_cell_index(
        query_idx, k=10,
        filters={"cell_type": "T cell", "AgeGroup": "Adult"}
    )
    print(engine.format_results(result2))

    # 演示 3: 条件过滤检索 (仅搜索 hepatocyte)
    print("\n--- 演示 3: 条件过滤检索 (仅搜索 hepatocyte) ---")
    result3 = engine.search_by_cell_index(
        query_idx, k=10,
        filters={"cell_type": "hepatocyte"}
    )
    print(engine.format_results(result3))

    # ======== 阶段 5: 性能基准 ========
    print("\n" + "=" * 75)
    print("  阶段 5: 性能基准测试")
    print("=" * 75)

    # 暴力搜索基准
    engine_brute = SearchEngine(use_vectors, metadata, method="brute")
    stats_brute = engine_brute.benchmark(n_queries=100, k=10)
    stats_brute_filtered = engine_brute.benchmark(
        n_queries=50, k=10,
        filters={"cell_type": "T cell"}
    )

    # FAISS 基准
    stats_faiss = engine.benchmark(n_queries=100, k=10)
    stats_faiss_filtered = engine.benchmark(
        n_queries=50, k=10,
        filters={"cell_type": "T cell"}
    )

    # 召回率测试
    print("\n--- 召回率对比 ---")
    _test_recall(engine_brute, engine, use_vectors, k=10, n_test=100)

    print("\n" + "=" * 75)
    print("  成员 B 任务完成! 所有模块运行正常 ✓")
    print("=" * 75)

    return dm, engine


def _test_recall(engine_brute: SearchEngine,
                  engine_ann: SearchEngine,
                  vectors: np.ndarray,
                  k: int = 10, n_test: int = 100):
    """测试 ANN 检索的召回率 (以暴力搜索为 ground truth)"""
    rng = np.random.RandomState(42)
    test_indices = rng.choice(len(vectors), size=min(n_test, len(vectors)),
                               replace=False)
    queries = vectors[test_indices]

    # Ground truth
    result_gt = engine_brute.search(queries, k=k, metric="cosine")
    # ANN
    result_ann = engine_ann.search(queries, k=k, metric="cosine")

    recalls = []
    for i in range(len(test_indices)):
        gt_set = set(result_gt.indices[i])
        ann_set = set(result_ann.indices[i])
        # 排除填充的 -1
        gt_set.discard(-1)
        ann_set.discard(-1)
        if len(gt_set) > 0:
            recall = len(gt_set & ann_set) / len(gt_set)
            recalls.append(recall)

    avg_recall = np.mean(recalls) if recalls else 0
    print(f"  FAISS vs Brute: 平均召回率@{k} = {avg_recall:.2%}")
    print(f"  暴力搜索平均耗时: {result_gt.query_time_ms:.2f}ms")
    print(f"  FAISS 平均耗时: {result_ann.query_time_ms:.2f}ms")
    if result_gt.query_time_ms > 0:
        print(f"  加速比: {result_gt.query_time_ms / max(result_ann.query_time_ms, 0.01):.1f}x")


def quick_search_demo():
    """快速检索演示 (无需完整预处理)"""
    print("=" * 60)
    print("  快速检索演示")
    print("=" * 60)

    dm = DataManager("liver.h5ad")
    dm.load_data()
    vectors = dm.get_pca_vectors(n_dims=64)
    metadata = dm.adata.obs.copy()

    engine = SearchEngine(vectors, metadata, method="brute")

    # 查询: 找与第 100 个细胞最相似的 5 个细胞
    result = engine.search_by_cell_index(100, k=5)
    print(engine.format_results(result))

    # 条件过滤: 找相似的 hepatocyte
    result_filtered = engine.search_by_cell_index(
        100, k=5,
        filters={"cell_type": "hepatocyte"}
    )
    print(engine.format_results(result_filtered))


if __name__ == "__main__":
    # 创建输出目录
    Path("output").mkdir(exist_ok=True)

    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_search_demo()
    else:
        demo_pipeline()
