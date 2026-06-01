# 单细胞 ANN 检索系统

> 软件工程大作业 — 5 人小组项目

---

## 项目结构

```
Software-Engineering-Major-Project-main/
├── 成员A文件/
│   ├── index_builder.py   — ANN 索引构建模块（成员 A）
│   ├── main_a.py          — 演示脚本（成员 A）
│   └── index_store/       — FAISS 索引保存目录（运行后生成）
├── 成员B文件/
│   ├── data_manager.py    — 数据读取与解析（成员 B）
│   ├── preprocessing.py   — 数据预处理（成员 B）
│   ├── search_engine.py   — 检索引擎（成员 B）
│   ├── main.py            — 成员 B 主控脚本
│   ├── cell_vectors.npy  — 输出给成员 A 的向量文件
│   └── cell_metadata.csv  — 细胞元信息
└── README.md
```

---

## 成员 A — ANN 索引构建（组长）

**职责**：ANN 索引构建 + 索引管理（构建/保存/加载）+ 项目管理

### 文件清单

| 文件 | 说明 |
|------|------|
| `index_builder.py` | 核心模块：`IndexManager` 类，支持 FAISS IVF / HNSW |
| `main_a.py` | 演示脚本：构建、保存、加载、查询完整流程 |
| `index_store/` | FAISS 索引保存目录（运行后生成） |
| `index_store_hnsw/` | HNSW 索引保存目录（运行后生成） |

### 环境安装

```bash
pip install numpy faiss-cpu hnswlib
# GPU 版（可选）：pip install faiss-gpu
```

### 快速运行

```bash
# 完整演示（构建 + 加载 + 查询 + 调参）
python main_a.py

# 仅构建并保存
python main_a.py build

# 仅加载并查询
python main_a.py search

# 方法性能对比（FAISS vs HNSW）
python main_a.py benchmark
```

### 对接成员 C（后端集成接口）

成员 C 在 Flask 后端中直接使用 `IndexManager`：

```python
from index_builder import IndexManager

# === 启动时初始化一次（全局单例）===
index_mgr = IndexManager("../成员B文件/cell_vectors.npy")
index_mgr.load("index_store")   # 加载已构建的 FAISS 索引

# === 检索接口 ===
# query_vec: np.ndarray, shape (30,) 或 (n_queries, 30)
distances, indices = index_mgr.search(query_vec, k=10)
# distances: (n_queries, k) 余弦相似度，越大越相似（1.0 = 完全相同）
# indices:   (n_queries, k) 细胞整数索引，与 cell_metadata.csv 的 cell_index 对应

# === 状态接口 ===
status = index_mgr.status()
# 返回: {"active_method", "n_cells", "n_dims", "faiss_ready", "hnsw_ready", ...}

# === 动态调参 ===
index_mgr.set_nprobe(20)    # 提高 FAISS 精度（nprobe 越大越准，查询越慢）
index_mgr.set_ef_search(80) # 提高 HNSW 精度
```

### 索引文件目录结构

```
index_store/
  faiss_ivf.index      — FAISS 索引二进制文件
  index_meta.json      — 元信息（方法、参数、维度等）

index_store_hnsw/
  hnsw.bin             — HNSW 索引二进制文件
  index_meta.json      — 元信息
```

### 两种索引对比

| 方法 | 构建耗时 | 查询耗时 | 召回率@10 | 内存占用 | 推荐场景 |
|------|---------|---------|----------|---------|---------|
| **FAISS IVF** | ~0.06s | ~0.3ms | ~100% | 低 | 优先使用，精度高 |
| **HNSW** | ~0.53s | ~0.2ms | ~99% | 较高 | 追求极致速度 |

> 69,032 个细胞、30 维 PCA 向量测试结果

### 注意事项

1. **向量格式**：`cell_vectors.npy` 必须是 `float32`，已 L2 归一化
2. **索引复用**：索引构建一次后保存到磁盘，后续启动直接 `load()`，无需重建
3. **返回的 indices 与成员 B 的 cell_index 一一对应**，可直接用于 `cell_metadata.csv` 查询细胞信息
4. **条件过滤**：本模块只做纯向量检索，条件过滤逻辑在成员 B 的 `SearchEngine` 中实现，成员 C 按需选用

---

## 成员 B — 数据处理 + 检索引擎

**职责**：数据读取与解析、数据预处理、向量输出、Top-K 检索、条件过滤检索

### 具体负责内容

| 序号 | 任务模块 | 具体内容 |
|------|---------|---------|
| 1 | 数据读取与解析 | 读取单细胞数据（`.h5ad` / AnnData 格式），理解数据结构 |
| 2 | 数据预处理 | 质量控制（QC）、标准化、对数变换、高变基因筛选、PCA 降维 |
| 3 | 向量输出 | 生成低维细胞向量，输出给成员 A 构建索引（`.npy` 格式，float32） |
| 4 | Top-K 检索 | 实现相似细胞检索，返回 top-k 个最相近结果及细胞信息 |
| 5 | 条件过滤检索 | 支持按细胞类型等条件过滤后再检索（结项要求） |
| 6 | 检索参数设置 | 支持 K 值、距离度量等参数配置 |
| 7 | 接口对接 | 封装检索函数，供成员 C（后端 API）调用 |
| 8 | 文档撰写 | 负责「需求分析」和「数据库设计」章节 |

### 中期交付（6月1日前）

- [x] 数据读取 + PCA 降维流程跑通
- [x] 输出向量给成员 A 完成索引构建
- [x] 实现基础 Top-K 检索

### 结项交付（7月12日前）

- [ ] 条件过滤检索功能
- [ ] 完成负责的文档章节
- [ ] 配合完成性能评估与测试

---

## 运行顺序（首次）

1. **成员 B**：运行 `preprocessing.py` 生成 `cell_vectors.npy`
2. **成员 A**：运行 `main_a.py build` 构建并保存索引
3. **成员 C**：运行后端服务，调用 `IndexManager` 提供 API

> 首次之后，成员 A 和成员 C 只需 `load()` 加载已有索引，无需重新构建。
