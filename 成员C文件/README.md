# 成员 C：后端服务与 API 接口模块

## 一、模块简介

本模块为软件工程大作业“面向单细胞高维向量数据的近似最近邻（ANN）检索系统”的后端服务模块，由成员 C 负责开发。

后端基于 Flask 框架实现，主要为前端页面、数据处理模块和检索模块提供统一的 Web API 接口。当前版本已经实现数据集信息读取、Top-K 相似细胞检索、条件过滤检索、元数据字段取值查询、用户注册登录等基础功能。

本模块不直接读取原始 `.h5ad` 大文件，而是读取成员 B 已经处理好的数据文件：

```text
../成员B文件/data/cell_vectors.npy
../成员B文件/data/cell_metadata.csv
../成员B文件/data/cell_2d_coords.csv
```

其中：

* `cell_vectors.npy`：细胞 PCA 向量，用于相似细胞检索
* `cell_metadata.csv`：细胞元数据，用于返回细胞类型、疾病状态、年龄组、性别等信息
* `cell_2d_coords.csv`：二维坐标数据，用于前端可视化展示

当前测试数据规模：

```text
细胞数量：69032
向量维度：30
元数据行数：69032
二维坐标行数：69032
```

---

## 二、成员 C 负责内容

根据小组分工，成员 C 负责后端服务与 API 接口开发，具体包括：

1. Web 后端框架搭建
2. 用户注册、登录和用户管理模块
3. 前后端 API 接口设计与联调
4. 数据集管理相关接口
5. 查询检索接口封装
6. 条件检索接口支持
7. 软件文档中的系统设计、详细设计相关内容

---

## 三、项目目录结构

成员 C 文件夹结构如下：

```text
成员C文件/
├─ app.py
├─ requirements.txt
├─ README.md
├─ routes/
│  ├─ __init__.py
│  ├─ user.py
│  ├─ dataset.py
│  └─ query.py
├─ utils/
│  ├─ __init__.py
│  ├─ data_loader.py
│  └─ search_service.py
└─ models/
   ├─ __init__.py
   └─ users.json
```

各文件说明：

| 文件                        | 作用                        |
| ------------------------- | ------------------------- |
| `app.py`                  | Flask 后端入口文件，负责注册路由并启动服务  |
| `routes/user.py`          | 用户注册、登录、用户列表、删除用户接口       |
| `routes/dataset.py`       | 数据集信息、数据状态、元数据字段取值接口      |
| `routes/query.py`         | Top-K 相似细胞检索接口            |
| `utils/data_loader.py`    | 读取细胞向量、元数据、二维坐标文件         |
| `utils/search_service.py` | 实现 L2 距离、cosine 距离和条件过滤检索 |
| `models/users.json`       | 简单保存用户信息，用于演示用户模块         |
| `requirements.txt`        | Python 依赖包列表              |

---

## 四、运行环境

推荐使用 Conda 环境运行。

### 1. 创建环境

```bash
conda create -n softann python=3.11 -y
```

### 2. 激活环境

```bash
conda activate softann
```

### 3. 安装依赖

进入成员 C 文件夹：

```bash
cd 成员C文件
pip install -r requirements.txt
```

`requirements.txt` 内容如下：

```text
Flask
Flask-Cors
numpy
pandas
```

---

## 五、启动后端服务

进入项目中的成员 C 文件夹：

```bash
cd /d E:\softteamwork\Software-Engineering-Major-Project\成员C文件
conda activate softann
python app.py
```

启动成功后，终端会显示：

```text
Running on http://127.0.0.1:5000
```

浏览器访问：

```text
http://127.0.0.1:5000
```

---

## 六、API 接口说明

### 1. 后端健康检查接口

请求：

```http
GET /api/health
```

示例：

```bash
curl http://127.0.0.1:5000/api/health
```

返回示例：

```json
{
  "message": "Flask 后端运行正常",
  "status": "ok"
}
```

---

### 2. 数据集信息接口

请求：

```http
GET /api/dataset/info
```

示例：

```bash
curl http://127.0.0.1:5000/api/dataset/info
```

返回示例：

```json
{
  "success": true,
  "data": {
    "dataset_name": "liver processed dataset",
    "vector_file": "cell_vectors.npy",
    "metadata_file": "cell_metadata.csv",
    "cell_count": 69032,
    "vector_dim": 30,
    "metadata_rows": 69032,
    "metadata_columns": [
      "cell_index",
      "cell_type",
      "disease",
      "donor_age",
      "sex",
      "nCount_RNA",
      "nFeature_RNA",
      "percent.mt",
      "Phase",
      "AgeGroup"
    ],
    "has_2d_coords": true,
    "coord_rows": 69032
  }
}
```

---

### 3. 数据集状态接口

请求：

```http
GET /api/dataset/status
```

示例：

```bash
curl http://127.0.0.1:5000/api/dataset/status
```

返回示例：

```json
{
  "success": true,
  "status": "loaded",
  "cell_count": 69032,
  "vector_dim": 30,
  "message": "数据集已加载，后端可执行 Top-K 检索"
}
```

---

### 4. 元数据字段取值接口

该接口用于查看某个元数据字段有哪些可选值，方便前端制作筛选下拉框。

请求格式：

```http
GET /api/dataset/column/<字段名>/values
```

查看年龄组：

```bash
curl http://127.0.0.1:5000/api/dataset/column/AgeGroup/values
```

返回示例：

```json
{
  "column": "AgeGroup",
  "count": 2,
  "success": true,
  "values": [
    "Adult",
    "Ped"
  ]
}
```

查看细胞类型：

```bash
curl http://127.0.0.1:5000/api/dataset/column/cell_type/values
```

返回示例：

```json
{
  "column": "cell_type",
  "count": 19,
  "success": true,
  "values": [
    "Kupffer cell",
    "T cell",
    "cholangiocyte",
    "conventional dendritic cell",
    "cycling myeloid cell",
    "cycling plasma cell",
    "endothelial cell of hepatic sinusoid",
    "erythrocyte",
    "gamma-delta T cell",
    "hematopoietic stem cell",
    "hepatocyte",
    "macrophage",
    "mature B cell",
    "mononuclear phagocyte",
    "natural killer cell",
    "neutrophil",
    "plasma cell",
    "platelet",
    "unknown"
  ]
}
```

---

### 5. Top-K 相似细胞检索接口

请求：

```http
POST /api/search
Content-Type: application/json
```

请求体：

```json
{
  "cell_index": 0,
  "top_k": 5,
  "metric": "l2"
}
```

测试命令：

```bash
curl -X POST http://127.0.0.1:5000/api/search ^
-H "Content-Type: application/json" ^
-d "{\"cell_index\":0,\"top_k\":5,\"metric\":\"l2\"}"
```

返回结果说明：

| 字段           | 含义           |
| ------------ | ------------ |
| `rank`       | 相似结果排名       |
| `cell_index` | 相似细胞在数据集中的索引 |
| `distance`   | 与查询细胞的距离     |
| `metadata`   | 该细胞对应的元数据信息  |

返回示例：

```json
{
  "success": true,
  "query_type": "cell_index",
  "query_cell_index": 0,
  "top_k": 5,
  "metric": "l2",
  "results": [
    {
      "rank": 1,
      "cell_index": 34749,
      "distance": 2.6974005699157715,
      "metadata": {
        "cell_type": "hepatocyte",
        "disease": "normal",
        "AgeGroup": "Ped",
        "sex": "male"
      }
    }
  ]
}
```

---

### 6. 条件过滤检索接口

条件过滤检索用于在指定元数据条件下返回 Top-K 相似细胞。例如：只在某个年龄组或某种细胞类型中检索。

#### 示例一：限定年龄组为 Ped

请求体：

```json
{
  "cell_index": 0,
  "top_k": 5,
  "metric": "l2",
  "filter_field": "AgeGroup",
  "filter_value": "Ped"
}
```

测试命令：

```bash
curl -X POST http://127.0.0.1:5000/api/search ^
-H "Content-Type: application/json" ^
-d "{\"cell_index\":0,\"top_k\":5,\"metric\":\"l2\",\"filter_field\":\"AgeGroup\",\"filter_value\":\"Ped\"}"
```

#### 示例二：限定细胞类型为 hepatocyte

请求体：

```json
{
  "cell_index": 0,
  "top_k": 5,
  "metric": "l2",
  "filter_field": "cell_type",
  "filter_value": "hepatocyte"
}
```

测试命令：

```bash
curl -X POST http://127.0.0.1:5000/api/search ^
-H "Content-Type: application/json" ^
-d "{\"cell_index\":0,\"top_k\":5,\"metric\":\"l2\",\"filter_field\":\"cell_type\",\"filter_value\":\"hepatocyte\"}"
```

---

### 7. 向量查询接口

除了通过 `cell_index` 查询，也可以直接传入查询向量。

请求体格式：

```json
{
  "query_vector": [0.1, 0.2, 0.3],
  "top_k": 5,
  "metric": "l2"
}
```

注意：当前数据向量维度为 30，因此 `query_vector` 必须是长度为 30 的一维数组。

---

## 七、用户管理接口

### 1. 用户注册

请求：

```http
POST /api/user/register
Content-Type: application/json
```

请求体：

```json
{
  "username": "test",
  "password": "123456",
  "role": "user"
}
```

测试命令：

```bash
curl -X POST http://127.0.0.1:5000/api/user/register ^
-H "Content-Type: application/json" ^
-d "{\"username\":\"test\",\"password\":\"123456\",\"role\":\"user\"}"
```

---

### 2. 用户登录

请求：

```http
POST /api/user/login
Content-Type: application/json
```

请求体：

```json
{
  "username": "test",
  "password": "123456"
}
```

测试命令：

```bash
curl -X POST http://127.0.0.1:5000/api/user/login ^
-H "Content-Type: application/json" ^
-d "{\"username\":\"test\",\"password\":\"123456\"}"
```

---

### 3. 用户列表

请求：

```http
GET /api/user/list
```

测试命令：

```bash
curl http://127.0.0.1:5000/api/user/list
```

---

### 4. 删除用户

请求：

```http
DELETE /api/user/delete/<user_id>
```

示例：

```bash
curl -X DELETE http://127.0.0.1:5000/api/user/delete/1
```

---

## 八、前后端联调说明

前端可以通过 JSON 请求调用后端接口。

### 查询接口示例

请求地址：

```text
http://127.0.0.1:5000/api/search
```

请求方法：

```text
POST
```

请求头：

```text
Content-Type: application/json
```

请求体：

```json
{
  "cell_index": 0,
  "top_k": 10,
  "metric": "l2",
  "filter_field": "cell_type",
  "filter_value": "hepatocyte"
}
```

前端展示时建议使用返回结果中的字段：

```text
results[i].rank
results[i].cell_index
results[i].distance
results[i].metadata.cell_type
results[i].metadata.disease
results[i].metadata.AgeGroup
results[i].metadata.sex
```

---

## 九、已完成测试

当前已经完成以下测试：

| 测试内容           | 接口                                     | 状态 |
| -------------- | -------------------------------------- | -- |
| 后端健康检查         | `/api/health`                          | 通过 |
| 数据集信息读取        | `/api/dataset/info`                    | 通过 |
| 年龄组字段取值        | `/api/dataset/column/AgeGroup/values`  | 通过 |
| 细胞类型字段取值       | `/api/dataset/column/cell_type/values` | 通过 |
| 普通 Top-K 检索    | `/api/search`                          | 通过 |
| AgeGroup 条件检索  | `/api/search`                          | 通过 |
| cell_type 条件检索 | `/api/search`                          | 通过 |

---

## 十、注意事项

1. 不要将原始 `.h5ad` 大文件提交到 GitHub。
2. 不要随意提交 `.npy`、`.csv` 等大数据文件，除非小组统一要求。
3. 当前用户信息保存在 `models/users.json`，主要用于课程作业演示，不适合作为正式生产环境用户系统。
4. 当前检索方式为基于 NumPy 的线性 Top-K 检索，后续可继续对接成员 A 的 FAISS / HNSWLIB 索引模块，提高查询性能。
5. 条件过滤字段必须和元数据字段完全一致，例如：

   * `AgeGroup`
   * `cell_type`
   * `disease`
   * `sex`
6. 条件过滤值区分大小写，例如：

   * `Adult`
   * `Ped`
   * `hepatocyte`

---

## 十一、后续可扩展方向

后续可以继续扩展以下功能：

1. 对接 FAISS / HNSWLIB，实现真正的 ANN 近似最近邻检索
2. 增加数据集上传、删除和动态索引更新接口
3. 增加 JWT 登录认证
4. 增加管理员权限校验
5. 增加接口响应时间统计
6. 增加查询日志记录
7. 与成员 D 前端可视化页面联调
8. 支持在 UMAP 可视化图上点击细胞并发起查询
