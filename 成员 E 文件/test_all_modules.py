# -*- coding: utf-8 -*-
"""
成员 E - 系统功能测试用例
===========================
测试范围：
1. 成员 A - ANN 索引构建模块 (index_builder.py)
2. 成员 B - 检索引擎 (search_engine.py)
3. 成员 C - 后端 API 服务 (app.py)

使用方法：
    cd Software-Engineering-Major-Project-main
    python 成员 E 文件/test_all_modules.py
"""

import os
import sys
import time
import unittest
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# ===================== 测试配置 =====================

# 项目根目录（使用绝对路径）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 测试数据路径（注意：目录名称是"成员B文件"，没有空格）
TEST_DATA_DIR = PROJECT_ROOT / "成员B文件" / "data"
CELL_VECTORS_PATH = TEST_DATA_DIR / "cell_vectors.npy"
CELL_METADATA_PATH = TEST_DATA_DIR / "cell_metadata.csv"

# 索引保存目录
INDEX_STORE_DIR = PROJECT_ROOT / "成员A文件" / "index_store_test"

print(f"Project Root: {PROJECT_ROOT}")
print(f"Test Data Dir: {TEST_DATA_DIR}")

# ===================== 测试工具函数 =====================

def load_test_data():
    """加载测试数据"""
    vectors = np.load(str(CELL_VECTORS_PATH))
    metadata = pd.read_csv(str(CELL_METADATA_PATH))
    return vectors, metadata


def generate_random_query_vector(vectors, n_queries=1):
    """生成随机查询向量"""
    n_dims = vectors.shape[1]
    query = np.random.randn(n_queries, n_dims).astype(np.float32)
    query = query / np.linalg.norm(query, axis=1, keepdims=True)
    return query


# ===================== 成员 A 测试用例 =====================

class TestMemberA_IndexBuilder(unittest.TestCase):
    """成员 A - ANN 索引构建模块测试"""
    
    @classmethod
    def setUpClass(cls):
        print("\n" + "="*60)
        print("成员 A - ANN 索引构建模块测试")
        print("="*60)
        
        cls.vectors, cls.metadata = load_test_data()
        print(f"加载测试数据：{cls.vectors.shape[0]} 个细胞，{cls.vectors.shape[1]} 维向量")
        
        sys.path.insert(0, str(PROJECT_ROOT / "成员A文件"))
        from index_builder import IndexManager
        cls.IndexManager = IndexManager
        
        import shutil
        if INDEX_STORE_DIR.exists():
            shutil.rmtree(INDEX_STORE_DIR)
    
    def test_01_initialization(self):
        """测试 1: IndexManager 初始化"""
        print("\n[测试 1] IndexManager 初始化")
        mgr = self.IndexManager(str(CELL_VECTORS_PATH))
        self.assertEqual(mgr.n_cells, self.vectors.shape[0])
        self.assertEqual(mgr.n_dims, self.vectors.shape[1])
        print(f"[OK] IndexManager 初始化成功")
    
    def test_02_faiss_build(self):
        """测试 2: FAISS 索引构建"""
        print("\n[测试 2] FAISS 索引构建")
        mgr = self.IndexManager(str(CELL_VECTORS_PATH))
        mgr.build(method="faiss_ivf", nlist=100)
        self.assertEqual(mgr._active_method, "faiss_ivf")
        self.assertIsNotNone(mgr._faiss_index)
        print(f"[OK] FAISS 索引构建完成")
    
    def test_03_search(self):
        """测试 3: FAISS 查询"""
        print("\n[测试 3] FAISS 查询")
        mgr = self.IndexManager(str(CELL_VECTORS_PATH))
        mgr.build(method="faiss_ivf", nlist=100)
        mgr.save(str(INDEX_STORE_DIR))
        
        mgr2 = self.IndexManager(str(CELL_VECTORS_PATH))
        mgr2.load(str(INDEX_STORE_DIR), method="faiss_ivf")
        
        query = generate_random_query_vector(self.vectors)
        distances, indices = mgr2.search(query, k=10)
        
        self.assertEqual(distances.shape, (1, 10))
        self.assertEqual(indices.shape, (1, 10))
        print(f"[OK] FAISS 查询成功")
    
    @classmethod
    def tearDownClass(cls):
        import shutil
        if INDEX_STORE_DIR.exists():
            shutil.rmtree(INDEX_STORE_DIR)


# ===================== 成员 B 测试用例 =====================

class TestMemberB_SearchEngine(unittest.TestCase):
    """成员 B - 检索引擎测试"""
    
    @classmethod
    def setUpClass(cls):
        print("\n" + "="*60)
        print("成员 B - 检索引擎测试")
        print("="*60)
        
        cls.vectors, cls.metadata = load_test_data()
        print(f"加载测试数据：{cls.vectors.shape[0]} 个细胞")
        
        sys.path.insert(0, str(PROJECT_ROOT / "成员B文件" / "code"))
        from search_engine import SearchEngine
        cls.SearchEngine = SearchEngine
    
    def test_01_initialization(self):
        """测试 1: SearchEngine 初始化"""
        print("\n[测试 1] SearchEngine 初始化")
        engine = self.SearchEngine(self.vectors, self.metadata, method="faiss")
        self.assertEqual(engine.n_cells, self.vectors.shape[0])
        print(f"[OK] SearchEngine 初始化成功")
    
    def test_02_index_build(self):
        """测试 2: 索引构建"""
        print("\n[测试 2] 索引构建")
        engine = self.SearchEngine(self.vectors, self.metadata, method="faiss")
        engine.build_index(nlist=100)
        self.assertTrue(engine._index_built)
        print(f"[OK] 索引构建完成")
    
    def test_03_search(self):
        """测试 3: 检索"""
        print("\n[测试 3] 检索")
        engine = self.SearchEngine(self.vectors, self.metadata, method="faiss")
        engine.build_index(nlist=100)
        
        query = generate_random_query_vector(self.vectors)
        result = engine.search(query, k=10)
        
        self.assertEqual(len(result.metadata[0]), 10)
        print(f"[OK] 检索成功，返回{len(result.metadata[0])}个结果")
    
    def test_04_filtered_search(self):
        """测试 4: 条件过滤检索"""
        print("\n[测试 4] 条件过滤检索")
        engine = self.SearchEngine(self.vectors, self.metadata, method="faiss")
        engine.build_index(nlist=100)
        
        query = generate_random_query_vector(self.vectors)
        result = engine.search(query, k=5, filters={"cell_type": "T cell"})
        
        self.assertGreater(len(result.metadata[0]), 0)
        print(f"[OK] 条件过滤检索成功")


# ===================== 成员 C 测试用例 =====================

class TestMemberC_BackendAPI(unittest.TestCase):
    """成员 C - 后端 API 服务测试"""
    
    @classmethod
    def setUpClass(cls):
        print("\n" + "="*60)
        print("成员 C - 后端 API 服务测试")
        print("="*60)
        
        sys.path.insert(0, str(PROJECT_ROOT / "成员C文件"))
        from app import create_app
        cls.app = create_app()
        cls.client = cls.app.test_client()
        print(f"[OK] Flask 应用创建成功")
    
    def test_01_health(self):
        """测试 1: 健康检查"""
        print("\n[测试 1] 健康检查")
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        print(f"[OK] 健康检查通过")
    
    def test_02_dataset_info(self):
        """测试 2: 数据集信息"""
        print("\n[测试 2] 数据集信息")
        response = self.client.get("/api/dataset/info")
        self.assertEqual(response.status_code, 200)
        print(f"[OK] 数据集信息获取成功")
    
    def test_03_search_api(self):
        """测试 3: 检索 API"""
        print("\n[测试 3] 检索 API")
        vectors, _ = load_test_data()
        query = generate_random_query_vector(vectors)
        
        response = self.client.post(
            "/api/search",
            json={"query": query[0].tolist(), "k": 10},
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        print(f"[OK] 检索 API 测试成功")


# ===================== 主函数 =====================

if __name__ == "__main__":
    print("="*80)
    print(" " * 25 + "单细胞 ANN 检索系统 - 功能测试套件")
    print(" " * 30 + "成员 E 负责模块")
    print("="*80)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestMemberA_IndexBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestMemberB_SearchEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestMemberC_BackendAPI))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*80)
    print("测试执行摘要")
    print("="*80)
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total - failures - errors
    
    print(f"总测试数：{total}")
    print(f"成功：{successes}")
    print(f"失败：{failures}")
    print(f"错误：{errors}")
    if total > 0:
        print(f"成功率：{successes/total*100:.1f}%")
    
    if result.wasSuccessful():
        print("\n所有测试通过！")
    else:
        print("\n部分测试失败，请查看上方详情")
    
    sys.exit(0 if result.wasSuccessful() else 1)
