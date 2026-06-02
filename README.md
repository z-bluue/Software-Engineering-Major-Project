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
│   ├── code/
│   │   ├── data_manager.py      — 数据管理模块
│   │   ├── preprocessing.py     — 预处理流水线
│   │   ├── search_engine.py     — 检索引擎
│   │   └── main.py              — 主控整合脚本
│   ├── data/
│   │   ├── cell_vectors.npy     — PCA 向量 → 成员 A
│   │   ├── cell_metadata.csv    — 细胞元数据 → 成员 C/D
│   │   ├── cell_2d_coords.csv   — UMAP 坐标 → 成员 D
│   │   ├── full_vectors.npy     — 全量向量 → 成员 E
│   │   ├── full_metadata.csv    — 全量元数据 → 成员 E
│   │   ├── processed_cell_vectors.npy — 新算 PCA 向量
│   │   └── liver.h5ad           — 原始数据
│   ├── 说明.md                  — 对接说明文档
│   └── 原始数据说明.md              — 原始数据字段说明
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

程伟卿 2311865 3075998327@qq.com

**职责**：数据读取与解析、数据预处理、向量输出、Top-K 检索、条件过滤检索

### 具体负责内容

| 序号 | 任务模块 | 具体内容 | 状态 |
|------|---------|---------|:--:|
| 1 | 数据读取与解析 | 读取 `.h5ad` / AnnData 格式，校验字段完整性 | ✅ |
| 2 | 数据预处理 | QC 过滤 → 标准化 → log1p 变换 → HVG(2000) → 缩放 → PCA(64) | ✅ |
| 3 | 向量输出 | 输出 PCA 向量 `.npy` (float32)，供成员 A 构建索引 | ✅ |
| 4 | Top-K 检索 | 支持暴力搜索 / FAISS IVF / HNSW 三种方法，返回细胞信息 | ✅ |
| 5 | 条件过滤检索 | 按 cell_type、AgeGroup 等任意字段过滤后检索，自动回退保证准确率 | ✅ |
| 6 | 检索参数设置 | 支持 K 值、距离度量（cosine/euclidean）、索引参数调优 | ✅ |
| 7 | 接口对接 | 封装 `SearchEngine` 类供成员 C 调用，`说明.md` 含 Flask 集成示例 | ✅ |
| 8 | 文档撰写 | 负责「需求分析」和「数据库设计」章节 | ⬜ |

### 技术实现概要

**数据规模**: 69,032 个细胞 × 32,397 个基因，19 种细胞类型

**预处理流水线**:
```
原始数据 → QC(保留61K细胞) → 标准化(10K/library) → log1p
→ 高变基因筛选(2000 HVG) → Z-score缩放 → PCA(64维, 解释方差36.25%)
```

**检索性能**（30 维 PCA, 69K 细胞）:

| 方法 | 单查询耗时 | 召回率@10 | 说明 |
|------|-----------|----------|------|
| 暴力搜索 | ~1.5ms | 100% | 基准，适合小规模条件过滤 |
| FAISS IVF | ~0.3ms | 100% | 推荐，精度高 + 速度快 |
| HNSW | ~0.2ms | ~99% | 极致速度，内存稍高 |

**条件过滤策略**: 当候选集占比 <30% 时自动回退暴力搜索，确保 ANN 索引不会漏掉跨类型匹配。

### 对接说明

#### → 成员 A（索引构建）

| 文件 | `data/cell_vectors.npy` |
|------|-------------------|
| **格式** | NumPy `.npy`，`float32` |
| **形状** | `(69032, 30)` — 69,032 个细胞 × 30 维 PCA |
| **语义** | 每行一个细胞的低维嵌入向量，已 L2 归一化（余弦相似度 = 内积） |
| **加载** | `vectors = np.load("data/cell_vectors.npy")` |
| **建议索引** | FAISS `IndexIVFFlat` + `METRIC_INNER_PRODUCT`，nlist=100~200 |

#### → 成员 C（后端 API）

核心类是 `search_engine.py` 中的 `SearchEngine`，提供两种调用方式：

```python
from search_engine import SearchEngine

# 方式 1：直接使用 SearchEngine（含元数据返回）
engine = SearchEngine(vectors, metadata, method="faiss")  # code/search_engine.py
engine.build_index(nlist=100)
result = engine.search(query_vec, k=10, filters={"cell_type": "T cell"})
# result.metadata[0] → [{rank, cell_index, score, cell_type, ...}, ...]

# 方式 2：配合成员 A 的 IndexManager（纯向量检索 + 自行查元数据）
distances, indices = index_mgr.search(query_vec, k=10)
cell_info = metadata.iloc[indices[0]]  # 从 cell_metadata.csv 查详细信息
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `query` | `np.ndarray (d,)` 或 `(n, d)` | 查询向量，自动 L2 归一化 |
| `k` | `int` | 返回数量，默认 10 |
| `filters` | `dict` 或 `None` | 如 `{"cell_type": "hepatocyte", "AgeGroup": "Adult"}` |
| `metric` | `str` | `"cosine"`（默认）或 `"euclidean"` |

返回的 `SearchResult` 结构见 `成员B文件/说明.md` 第四章。

#### → 成员 D（可视化）

| 文件 | `data/cell_2d_coords.csv` |
|------|---------------------|
| **格式** | CSV，含表头 |
| **列** | `cell_index, umap_1, umap_2, cell_type, disease, AgeGroup` |
| **用途** | `umap_1/umap_2` 为 UMAP 降维坐标，`cell_type` 用于着色 |

```python
df = pd.read_csv("data/cell_2d_coords.csv")
# 按 cell_type 分组绘图即可得到细胞分布散点图
```

#### → 成员 E（性能评估）

| 文件 | 格式 | 用途 |
|------|------|------|
| `data/full_vectors.npy` | `(69032, 30)` float32 | 全量 PCA 向量，构建 ground truth |
| `data/full_metadata.csv` | CSV, 55 列 | 全量元数据，含所有 obs 字段 |

`search_engine.py` 已内置 `benchmark()` 方法，可直接调用获取耗时/吞吐量数据。召回率对比参考 `main.py` 中的 `_test_recall()` 函数。

### 中期交付（6月1日前）

- [x] 数据读取 + PCA 降维流程跑通
- [x] 输出向量给成员 A 完成索引构建
- [x] 实现基础 Top-K 检索

### 结项交付（7月12日前）

- [x] 条件过滤检索功能（已提前完成）
- [ ] 完成负责的文档章节（需求分析 + 数据库设计）
- [ ] 配合成员 E 完成性能评估与测试

---

## 运行顺序（首次）

1. **成员 B**：运行 `code/preprocessing.py` 生成 `data/cell_vectors.npy`
2. **成员 A**：运行 `main_a.py build` 构建并保存索引
3. **成员 C**：运行后端服务，调用 `IndexManager` 提供 API

> 首次之后，成员 A 和成员 C 只需 `load()` 加载已有索引，无需重新构建。
