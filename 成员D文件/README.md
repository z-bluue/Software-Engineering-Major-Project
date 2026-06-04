# 成员 D：前端展示与可视化模块

## 一、模块简介

本模块为软件工程大作业“单细胞 ANN 检索系统”的 **前端展示与可视化模块**，由成员 D 负责开发。

前端采用了当前主流的技术栈和开箱即用的无需编译设计：
- **核心框架**：Vue 3.x（通过 CDN 引入，免去复杂的 Node.js 原生编译打包流）
- **UI 组件库**：Element Plus
- **前端网络请求**：Axios
- **可视化库**：ECharts
- **本地 CSV 数据解析**：PapaParse

前端界面具备如下能力：
1. **API 状态侦定与系统感知**：能够自动连通成员 C 提供的 Flask 引擎并获取 `dataset_info`。
2. **检索参数设置面板**：支持配置基于 Target Cell 的 Top-K 检索、距离度量（l2/cosine）。
3. **带联动的条件过滤检索**：可选择指定过滤属性（如 `cell_type` 或 `AgeGroup`），触发动态查询并锁定可用值列表供用户下发。
4. **大屏交互高可用散点渲染**：69,032 个细胞数据的高效 UMAP 聚合渲染（使用 ECharts 的 `large` 模式优化绘制过程）。
5. **检索结果数据表格与可视化双向标注**：执行 ANN 后侧边栏产生排位序列表，图表中自动生成「红色中心红点」锁定靶细胞位置并高亮黄圈标出全部相似检索项。

## 二、文件结构

```
成员D文件/
├── index.html       # 网站唯一入口，静态化网页架构体系与资源引入
├── app.js           # Vue 3 的核心业务逻辑抽象、轴点配置与 ECharts 渲染控制
├── styles.css       # 相关全局与局部卡片排版 CSS 重构预设
└── README.md        # 现行规范与结构文档（本文档）
```

## 三、如何运行加载

因为采用了免打包的前端部署结构配置模块，但也需要通过 Web Server（处理 HTTP 协议）才能绕过各大浏览器默认本地文件 `CORS(Cross-Origin Resource Sharing)` 协议阻止与 `PapaParse` 读取同级文件的限制。

1. **首先必须开启成员 C 的后端服务**
请在所在环境根据成员 C 里的指南，启动 Flask 引擎 `python app.py`。
*(验证接口 `http://127.0.0.1:5000/api/dataset/info` 开放正常)*

2. **在项目根目录下创建一个网页基础服务端口**
确保您通过终端切入整个项⽬的 **总根⽬褰（软件工程 - Software-Engineering-Major-Project）**，运行基础的 Python 静态服务：
```bash
python -m http.server 8000
```

3. **进入浏览器验收使用**
打开浏览器访问进入本系统的 Web UI：
[http://localhost:8000/成员D文件/index.html](http://localhost:8000/成员D文件/index.html)