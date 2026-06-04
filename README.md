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

## 成员 C — 后端服务与 API 接口模块

**职责**：基于 Flask 搭建后端 API 路由架构，串联检索算法与数据读取模块，向前端屏蔽底层逻辑，提供纯粹的高可用 RESTful API 查询管线。

### 架构设计特色（动静分离实践）
为避免 69,032 个坐标点生成出多达几万条记录的超大型 JSON，后端 **被严格限制了计算范围**，绝不进行可视化散点图的读取下发，把静态大文件的传输留给专门的静态服务器引擎；后端**仅专注高并发请求下处理高维度 ANN 相似度计算（如 L2 / Cosine）和 Top-K 数据提取**，彻底防备了前后端被网络传输带宽阻塞、甚至引发内存溢出的血崩缺陷。

### 功能清单
- **状态侦定**：提供 `GET /api/dataset/info` 让外部随时探知后端的联通态。
- **检索内核**：`POST /api/search` 接收指定靶向细胞或条件，配合 Fauna/FAISS/线性扫描 计算并返回目标 Top-k 目标信息距离列。
- **属性联动**：`GET /api/dataset/column/<column_name>/values` 动态获取疾病、类型、年龄组的可选项配合用户页面筛选。
- **账户系统**：(基础Demo) 使用预置 JSON 管控登陆注册认证。

---

## 成员 D — 前端展示与可视化模块

**职责**：Web UI 构建方案、API 集成对接流、用户交互状态机与高可用超大规模可视化图表渲染。

### 架构设计特色 (极致工业级页面性能优化)
采用了最新现代无打包前端架构（CDN + Vue 3 + Element Plus），去除了臃肿的 Node 依赖，直接部署为轻量化原生应用形态。

1. **大屏视图极限渲染优化**：利用 ECharts WebGL `large` 模式成功在网页上平滑聚合 6.9万高维解析散点。并且自主开发了**线性平滑防颤抖算法（Math.round关联倍率）**抑制了海量渲染由于坐标突跳造成的死机和频闪现象。
2. **检索查询视角零状态破坏**：攻克 ECharts `replaceMerge` 与底层画布数据更新结合的问题，重构分离式数据管线：任何高频搜索、靶细胞标记产生，用户的页面变焦大小与镜头边界状态都不会发生破裂丢失。
3. **极其严酷的 FlexBox 排版限制机制**：使用 HTML 原生死锁弹性盒子配合限制容器（100vh），无论从后端涌入几十还是上百条相似结果表格，只会在左侧面板内部生成卷轴，拒绝了低劣的传统网页全局被无限撑底溢出。
4. **前端直读纯静态加速**：使用了 Web Worker 相关的 `PapaParse` 技术从本地服务直读冷数据，加速 10x 等级，完美对应成员 C 后端不挂载该重活的高级方案。 

---

## 运行说明

### 📦 前置条件

```bash
# 安装所有依赖
pip install numpy pandas faiss-cpu hnswlib flask flask-cors scikit-learn
```

### 🚀 快速启动（非首次运行）

**终端 1 - 启动后端服务：**
```bash
cd 成员C文件
python app.py
# 服务运行在：http://127.0.0.1:5000
```

**终端 2 - 启动前端服务器（新建终端窗口）：**
```bash
cd Software-Engineering-Major-Project-main
python -m http.server 8000
# 服务运行在：http://localhost:8000
```

**访问可视化界面：**
```
http://localhost:8000/成员D文件/index.html
```

### 📋 首次运行（完整流程）

#### 步骤 1：生成向量数据（仅首次需要）
```bash
cd 成员B文件/code
python preprocessing.py
# 生成：cell_vectors.npy, cell_metadata.csv, cell_2d_coords.csv
```

#### 步骤 2：构建 ANN 索引（仅首次需要）
```bash
cd 成员A文件
python main_a.py build
# 生成：index_store/ 目录（FAISS 索引）
```

#### 步骤 3：启动服务（同上快速启动步骤）

### 🖥️ 启动命令速查表

| 步骤 | 命令 | 说明 |
|------|------|------|
| 后端服务 | `cd 成员C文件 && python app.py` | 运行在 http://127.0.0.1:5000 |
| 前端服务器 | `cd Software-Engineering-Major-Project-main && python -m http.server 8000` | 运行在 http://localhost:8000 |
| 可视化界面 | 浏览器访问 `http://localhost:8000/成员D文件/index.html` | 打开交互界面 |

### 服务状态检查

| 服务 | 地址 | 检查命令 |
|------|------|---------|
| 后端 API | http://127.0.0.1:5000 | `curl http://127.0.0.1:5000/api/health` |
| 前端服务器 | http://localhost:8000 | 浏览器访问 |

### 界面功能说明

成功启动后，可视化界面包含：

1. **顶部状态栏**
   - `Backend Online`：后端连接成功（绿色）
   - `数据集装载：69032 细胞`：数据加载状态

2. **左侧检索面板**
   - 图例分类：选择着色依据（细胞类型/疾病状态/年龄阶段）
   - 目标细胞 Index：输入 0-69031 之间的细胞索引
   - Top-K 返回数量：设置返回最近邻数量（1-100）
   - 距离度量：选择 Cosine 或 L2 距离
   - 条件过滤：按字段筛选检索范围
   - 立即检索：执行 ANN 近似最近邻搜索

3. **右侧可视化区域**
   - UMAP 细胞分布图：69,032 个细胞的降维可视化
   - 检索结果高亮：红色标记目标细胞，黄色标记检索结果
   - 缩放控制：支持鼠标滚轮缩放

4. **检索结果表格**
   - 显示排名、细胞索引、距离、细胞类型等信息

### 演示流程建议

1. 打开界面，等待数据加载完成（显示 "Backend Online"）
2. 设置目标细胞 Index（如：1000）
3. 设置 Top-K = 10
4. 点击「立即检索」按钮
5. 观察检索结果表格和 UMAP 图中的高亮显示
6. 尝试条件过滤（如：只检索 "T cell" 类型）
7. 尝试不同的图例分类查看细胞分布

### 常见问题

**Q1：前端显示 "Backend Offline"**
- 确保后端服务已启动：`cd 成员C文件 && python app.py`
- 检查端口 5000 是否被占用

**Q2：UMAP 图加载失败**
- 确保通过 `http://localhost:8000` 访问，不要直接打开本地文件
- 检查 `成员B文件/data/cell_2d_coords.csv` 文件是否存在

**Q3：检索按钮灰色不可点击**
- 等待数据加载完成（右上角显示数据集信息）
- 确保后端服务正常运行

### 性能指标

| 指标 | 值 |
|------|------|
| 细胞数量 | 69,032 |
| 向量维度 | 30 (PCA) |
| 查询响应时间 | < 1ms |
| 召回率@10 | 100% (FAISS IVF) |

---

## 项目文件结构

```
Software-Engineering-Major-Project-main/
├── 成员A文件/           # ANN 索引构建
│   ├── index_builder.py
│   ├── main_a.py
│   └── index_store/
├── 成员B文件/           # 数据处理 + 检索引擎
│   ├── code/
│   │   ├── data_manager.py
│   │   ├── preprocessing.py
│   │   ├── search_engine.py
│   │   └── main.py
│   └── data/
│       ├── cell_vectors.npy
│       ├── cell_metadata.csv
│       └── cell_2d_coords.csv
├── 成员C文件/           # 后端 API
│   ├── app.py
│   └── routes/
├── 成员D文件/           # 前端可视化
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── 成员E文件/           # 测试与性能评测
│   ├── test_all_modules.py
│   ├── performance_benchmark.py
│   └── doc_系统测试章节.md
└── README.md
```
