\documentclass[a4paper]{article}

\input{style/ch_xelatex.tex}
\input{style/scala.tex}

%代码段设置
\lstset{numbers=left,
basicstyle=\tiny,
numberstyle=\tiny,
keywordstyle=\color{blue!70},
commentstyle=\color{red!50!green!50!blue!50},
frame=single, rulesepcolor=\color{red!20!green!20!blue!20},
escapeinside=``
}

\graphicspath{ {images/} }
\usepackage{ctex}
\usepackage{graphicx}
\usepackage{color,framed}%文本框
\usepackage{listings}
\usepackage{caption}
\usepackage{amssymb}
\usepackage{enumerate}
\usepackage{xcolor}
\usepackage{bm} 
\usepackage{lastpage}%获得总页数
\usepackage{fancyhdr}
\usepackage{tabularx}  
\usepackage{geometry}
\usepackage{minted}
\usepackage{graphics}
\usepackage{subfigure}
\usepackage{float}
\usepackage{pdfpages}
\usepackage{pgfplots}
\pgfplotsset{width=10cm,compat=1.9}
\usepackage{multirow}
\usepackage{footnote}
\usepackage{booktabs}

%-----------------------伪代码------------------
\usepackage{algorithm}  
\usepackage{algorithmicx}  
\usepackage{algpseudocode}  
\floatname{algorithm}{Algorithm}  
\renewcommand{\algorithmicrequire}{\textbf{Input:}}  
\renewcommand{\algorithmicensure}{\textbf{Output:}} 
\usepackage{lipsum}  
\makeatletter
\newenvironment{breakablealgorithm}
  {% \begin{breakablealgorithm}
  \begin{center}
     \refstepcounter{algorithm}% New algorithm
     \hrule height.8pt depth0pt \kern2pt% \@fs@pre for \@fs@ruled
     \renewcommand{\caption}[2][\relax]{% Make a new \caption
      {\raggedright\textbf{\ALG@name~\thealgorithm} ##2\par}%
      \ifx\relax##1\relax % #1 is \relax
         \addcontentsline{loa}{algorithm}{\protect\numberline{\thealgorithm}##2}%
      \else % #1 is not \relax
         \addcontentsline{loa}{algorithm}{\protect\numberline{\thealgorithm}##1}%
      \fi
      \kern2pt\hrule\kern2pt
     }
  }{% \end{breakablealgorithm}
     \kern2pt\hrule\relax% \@fs@post for \@fs@ruled
  \end{center}
  }
\makeatother
%------------------------代码-------------------
\usepackage{xcolor} 
\usepackage{listings} 
\lstset{ 
breaklines,%自动换行
basicstyle=\small,
escapeinside=``,
keywordstyle=\color{ blue!70} \bfseries,
commentstyle=\color{red!50!green!50!blue!50},% 
stringstyle=\ttfamily,% 
extendedchars=false,% 
linewidth=\textwidth,% 
numbers=left,% 
numberstyle=\tiny \color{blue!50},% 
frame=trbl% 
rulesepcolor= \color{ red!20!green!20!blue!20} 
}

%-------------------------页面边距--------------
\geometry{a4paper,left=2.3cm,right=2.3cm,top=2.7cm,bottom=2.7cm}
%-------------------------页眉页脚--------------
\usepackage{fancyhdr}
\pagestyle{fancy}
\lhead{\kaishu \leftmark}
% \chead{}
\rhead{\kaishu 软件工程}%加粗\bfseries 
\lfoot{}
\cfoot{\thepage}
\rfoot{}
\renewcommand{\headrulewidth}{0.1pt}  
\renewcommand{\footrulewidth}{0pt}%去掉横线
\newcommand{\HRule}{\rule{\linewidth}{0.5mm}}%标题横线
\newcommand{\HRulegrossa}{\rule{\linewidth}{1.2mm}}
\setlength{\textfloatsep}{10mm}%设置图片的前后间距
%--------------------文档内容--------------------

\begin{document}
\renewcommand{\contentsname}{目\ 录}
\renewcommand{\appendixname}{附录}
\renewcommand{\appendixpagename}{附录}
\renewcommand{\refname}{参考文献} 
\renewcommand{\figurename}{图}
\renewcommand{\tablename}{表}
\renewcommand{\today}{\number\year 年 \number\month 月 \number\day 日}

%-------------------------封面----------------
\begin{titlepage}
    \begin{center}
    \includegraphics[width=0.8\textwidth]{NKU.png}\\[1cm]
    \vspace{20mm}
		\textbf{\huge\textbf{\kaishu{计算机学院}}}\\[0.5cm]
		\textbf{\huge{\kaishu{软件工程实验报告}}}\\[2.3cm]
		\textbf{\Huge\textbf{\kaishu{单细胞高维向量数据 ANN 检索系统需求分析报告}}}

		\vspace{\fill}
    
    \centering
      \textsc{\LARGE \kaishu{组别\ :\ 12}}\\[0.5cm]
      \textsc{\LARGE \kaishu{专业\ :\ 计算机科学与技术}}\\[0.5cm]
      {\small
      \textsc{\LARGE \kaishu{张瑞宸}}\\[0.5cm]
      \textsc{\LARGE \kaishu{李佳泽}}\\[0.5cm]
      \textsc{\LARGE \kaishu{李煦阳}}\\[0.5cm]
      \textsc{\LARGE \kaishu{程伟卿}}\\[0.5cm]
      \textsc{\LARGE \kaishu{陈华宇}}\\[0.5cm]
      }
    \vfill
    {\Large \today}
    \end{center}
\end{titlepage}

\renewcommand {\thefigure}{\thesection{}.\arabic{figure}}%图片按章标号
\renewcommand{\figurename}{图}
\renewcommand{\contentsname}{目录}  
\cfoot{\thepage\ of \pageref{LastPage}}%当前页 of 总页数


% 生成目录
\clearpage
\tableofcontents
\newpage

\section{引言}

\subsection{编写目的}
本文档为“单细胞近似最近邻（ANN）检索系统”的需求分析报告。编写此报告的主要目的在于：
\begin{itemize}
    \item \textbf{明确业务边界与功能范围：} 详尽地描述系统需实现的数据处理、核心检索与可视化展现等功能，消除开发过程中的需求歧义。
    \item \textbf{奠定系统设计基础：} 为后续的系统总体架构设计、数据库设计、以及前后端接口（API）规范提供明确的业务逻辑参考。
    \item \textbf{制定测试与验收基准：} 为测试团队编写测试用例提供依据，同时作为最终项目交付与大工作业考核的验收标准。
\end{itemize}
本文档的预期读者包括项目开发团队成员、系统测试人员、指导教师以及未来的系统维护人员。

\subsection{项目背景}
进入后基因组时代，单细胞测序技术（Single-cell Sequencing）迎来了爆发式发展。该技术能够将组织中的单个细胞分离出来，分别测量每个细胞内部的分子信息。经过测序与量化统计后，研究人员可以获得高通量的“细胞 $\times$ 基因”表达矩阵。在实际科研场景中，一个典型的单细胞实验往往会产生数万至数十万乃至上百万级别的细胞样本，经过特征提取（如 PCA、Harmony 等嵌入方法）后，每个细胞都被表征为一个高维特征向量。

面对如此庞大的高维向量数据集，传统的精确最近邻（Exact Nearest Neighbor, ENN）搜索算法（如线性扫描或 KD-Tree）暴露出严重的性能瓶颈，主要体现在面临“维数灾难”时查询效率极低、计算开销巨大、系统响应时间难以忍受。为了实现海量单细胞数据的快速比对与注释，系统亟需引入近似最近邻检索（Approximate Nearest Neighbor, ANN）技术。ANN 能够在容忍微小精度损失的前提下，通过构建特定的数据结构（如倒排索引、图索引等），将检索的时间复杂度呈指数级降低。因此，开发一套界面友好、检索高效的单细胞 ANN 检索系统，对于辅助生物信息学家进行细胞聚类、亚型发现以及疾病靶点分析具有重要的科研价值与工程意义。

\section{任务概述}

\subsection{任务目标}
本项目的核心目标是设计并开发一个面向单细胞高维向量数据的近似最近邻检索 Web 平台，打通从“原始数据文件”到“直观可视化分析”的完整链路。系统需实现以下关键目标：
\begin{itemize}
    \item \textbf{数据解析与规范化：} 支持标准单细胞数据格式（如 \texttt{.h5ad}）的解析，自动提取细胞元数据（Metadata）及指定的特征嵌入矩阵（如 \texttt{X\_harmony}）。
    \item \textbf{高性能索引构建：} 底层集成成熟的 ANN 算法库（如 Faiss），支持对高维特征向量进行快速索引构建、持久化存储与动态加载。
    \item \textbf{多维度联合检索：} 允许用户输入目标细胞 ID 或高维查询向量，结合 Top-K 参数及生物学条件（如细胞类型、组织来源等过滤条件），实现毫秒级的多模态相似性检索。
    \item \textbf{交互式可视化展示：} 提供直观的 Web UI 界面，不仅以数据表格形式展示近邻细胞的具体属性，还需集成二维降维图（如 UMAP），实现查询点及近邻点的动态高亮映射。
\end{itemize}

\subsection{用户特点}
本系统的目标受众与使用者主要划分为以下两类角色，各类角色具有不同的技术背景与操作诉求：
\begin{itemize}
    \item \textbf{科研用户（生物信息分析师/医学研究员）：}
    \begin{itemize}
        \item \textit{特点}：具备深厚的生物学和医学背景，但可能缺乏底层的计算机算法知识。
        \item \textit{诉求}：关注系统的易用性与直观性。他们需要简洁的表单来输入检索条件，高度依赖可视化的 UMAP 降维图来验证检索结果的生物学合理性（如查看相似细胞是否属于同一细胞亚型）。系统需屏蔽复杂的索引构建细节，做到“一键检索，即刻呈现”。
    \end{itemize}
    \item \textbf{系统管理员（平台运维人员）：}
    \begin{itemize}
        \item \textit{特点}：具备较强的 IT 运维能力和软件工程知识。
        \item \textit{诉求}：关注系统的稳定性与可控性。需要拥有最高权限，负责后台单细胞底层数据集的更新与导入、ANN 索引的预编译与缓存清理，以及平台注册用户的权限审核与日常管理。
    \end{itemize}
\end{itemize}

\subsection{假定与约束}
本系统的开发与运行将遵循以下前提假设与约束条件：
\begin{itemize}
    \item \textbf{环境约束：} 考虑到跨平台兼容性与部署便利性，系统整体采用 B/S（Browser/Server）架构设计。后端假定运行于配备充足内存及多核 CPU 的 Linux 服务器环境下，以支撑大规模矩阵运算；前端页面需兼容主流的现代 HTML5 浏览器（如 Chrome, Edge 等）。
    \item \textbf{数据约束：} 假定系统处理的输入文件为标准化的 \texttt{.h5ad} 格式文件，且文件内部已包含预处理后的高维嵌入矩阵及完整无误的细胞注释信息（如 \texttt{obs} 属性）。系统不负责处理原始 FASTQ 测序数据的比对与定量等极早期上游分析工作。
    \item \textbf{项目周期与合规约束：} 本系统作为软件工程大作业的核心交付物，必须在规定的截止日期（4月13日）前完成需求规格说明及相关 UML 建模文档的提交。系统文档规范需严格遵循 Nankai University 软件工程课程的标准与 UML 制图规范。
\end{itemize}

\section{业务描述}
系统总体业务流程描述如下：
\begin{enumerate}
    \item 用户通过Web浏览器访问系统，输入账号密码进行登录认证。
    \item 系统验证用户身份，根据用户角色（普通用户/管理员）展示相应的功能界面。
    \item 用户进入数据管理模块，上传单细胞表达矩阵文件（如CSV格式）。
    \item 系统对上传文件进行格式校验和基础预处理，解析为细胞×基因的高维向量数据，并存储于内存或数据库中。
    \item 用户进入索引构建模块，选择索引类型（如IVF、HNSW）和参数配置，发起索引构建任务。
    \item 系统根据选定的索引类型和参数，基于向量数据构建ANN索引，并保存索引文件至磁盘。
    \item 用户进入查询检索模块，选择查询方式（输入细胞编号或自定义向量）、设置检索参数（top-k、距离度量、索引类型等），提交查询请求。
    \item 系统加载对应索引，执行近似最近邻检索，返回top-k个相似细胞及其距离/相似度得分。
    \item 系统同时记录本次查询耗时、召回率（若与精确检索对比）等性能指标。
    \item 可视化展示模块将检索结果以表格和散点图形式呈现给用户。
    \item 用户可查看性能评测面板，对比不同参数配置下的检索效果。
    \item 管理员用户可额外进行用户管理操作，如添加、删除、修改用户信息。
\end{enumerate}

\subsection{各个子业务流程图及其描述}
\subsubsection{用户管理子流程}
用户管理子流程描述如下：
\begin{enumerate}
    \item \textbf{用户注册}：
    \begin{itemize}
        \item 新用户访问注册页面，填写用户名、密码、邮箱等必要信息。
        \item 系统校验用户名是否已存在，密码强度是否符合要求。
        \item 校验通过后，系统对密码进行加密处理，将用户信息存入数据库。
        \item 系统返回注册成功提示，引导用户跳转至登录页面。
    \end{itemize}
    \item \textbf{用户登录}：
    \begin{itemize}
        \item 用户在登录页面输入用户名和密码。
        \item 系统查询数据库验证用户凭证，检查账户状态（是否被禁用）。
        \item 验证通过后，系统生成会话（Session）或令牌（Token），跳转至系统主页面。
        \item 验证失败时，系统提示错误信息，允许用户重试或找回密码。
    \end{itemize}
    \item \textbf{用户信息管理（普通用户）}：
    \begin{itemize}
        \item 用户可查看个人信息，修改密码或邮箱。
        \item 系统验证原密码正确性后，更新数据库中的用户信息。
    \end{itemize}
    \item \textbf{用户管理（管理员）}：
    \begin{itemize}
        \item 管理员登录后进入用户管理页面，查看所有用户列表。
        \item 管理员可添加新用户、删除已有用户、修改用户角色（普通用户/管理员）。
        \item 管理员可禁用/启用用户账户，防止未授权访问。
        \item 所有用户管理操作均记录日志。
    \end{itemize}
    \item \textbf{用户注销}：
    \begin{itemize}
        \item 用户点击注销按钮，系统清除会话信息，返回登录页面。
    \end{itemize}
\end{enumerate}

\subsubsection{数据管理子流程}
数据管理子流程描述如下：
\begin{enumerate}
    \item \textbf{数据上传}：
    \begin{itemize}
        \item 用户通过Web界面选择本地数据文件（支持CSV、TSV、H5AD等格式）。
        \item 系统检查文件大小是否超过配置的上限（如500MB）。
        \item 文件大小合规后，系统将文件上传至服务器临时目录。
    \end{itemize}
    \item \textbf{格式校验}：
    \begin{itemize}
        \item 系统解析文件内容，检查是否为标准的矩阵格式。
        \item 校验行（细胞）和列（基因）的数量是否符合预期（行数≥1，列数≥1）。
        \item 检查数据单元格是否包含非数值内容或缺失值。
        \item 校验通过后进入预处理步骤；校验失败时返回具体错误信息，要求用户重新上传。
    \end{itemize}
    \item \textbf{数据预处理}：
    \begin{itemize}
        \item \textbf{缺失值处理}：若存在少量缺失值，系统使用均值或中位数填充，或删除包含缺失值的细胞/基因。
        \item \textbf{数据标准化/归一ization}：用户可选择对数据进行标准化（Z-score）或归一化（Min-Max），以消除基因表达量级的差异。
        \item \textbf{降维（可选）}：对于超高维数据（如超过5000维），用户可选择使用PCA等方法降维，减少后续检索的计算开销。
        \item 预处理完成后，系统展示数据摘要信息（细胞数量、基因数量、数据范围等），供用户确认。
    \end{itemize}
    \item \textbf{数据存储}：
    \begin{itemize}
        \item 预处理后的向量数据以NumPy数组或内存映射文件形式存储。
        \item 系统记录数据的元信息（如文件名、上传时间、数据维度、预处理参数）至数据库。
        \item 用户可为当前数据集命名，便于后续多数据集管理。
    \end{itemize}
    \item \textbf{数据管理操作}：
    \begin{itemize}
        \item 用户可查看已上传的数据集列表。
        \item 用户可选择切换当前活跃数据集，后续索引构建和检索均基于该数据集。
        \item 用户可删除不再需要的数据集，系统同时清理对应的向量文件和索引文件。
    \end{itemize}
\end{enumerate}

\subsubsection{索引构建子流程}
索引构建子流程描述如下：
\begin{enumerate}
    \item \textbf{索引类型选择}：
    \begin{itemize}
        \item 用户在当前活跃数据集上，选择要构建的索引类型。系统支持的索引类型包括：
        \begin{itemize}
            \item 线性扫描索引（精确检索基准，无需构建）
            \item IVF（Inverted File，倒排索引）
            \item HNSW（Hierarchical Navigable Small World）
            \item NSW（Navigable Small World）
            \item Annoy（Approximate Nearest Neighbors Oh Yeah）
        \end{itemize}
        \item 系统提示每种索引类型的适用场景和参数说明。
    \end{itemize}
    \item \textbf{参数配置}：
    \begin{itemize}
        \item 用户根据所选索引类型配置相应参数，常见参数包括：
        \begin{itemize}
            \item IVF：nlist（聚类中心数量）、nprobe（查询时探测的聚类数）
            \item HNSW：M（每个节点的最大连接数）、ef\_construction（构建时动态列表大小）
            \item Annoy：n\_trees（树的棵数）
        \end{itemize}
        \item 系统提供参数默认值，高级用户可手动调整。
    \end{itemize}
    \item \textbf{索引构建}：
    \begin{itemize}
        \item 用户点击“开始构建”按钮，系统启动索引构建任务。
        \item 系统读取当前数据集的向量数据，调用底层ANN库执行索引构建。
        \item 构建过程中，系统显示进度条和预计剩余时间。
        \item 构建完成后，系统计算并展示索引大小（内存占用）、构建耗时等统计信息。
    \end{itemize}
    \item \textbf{索引保存与加载}：
    \begin{itemize}
        \item 索引构建完成后，系统将索引序列化保存至磁盘文件。
        \item 索引元信息（索引类型、参数配置、构建时间、关联的数据集ID）存储至数据库。
        \item 系统启动或切换数据集时，可自动加载已存在的索引文件，避免重复构建。
    \end{itemize}
    \item \textbf{索引管理}：
    \begin{itemize}
        \item 用户可查看当前数据集下已构建的所有索引列表。
        \item 用户可删除不再需要的索引文件，释放磁盘空间。
        \item 用户可设置默认索引，查询时若不指定则使用默认索引。
    \end{itemize}
\end{enumerate}

\subsubsection{查询检索子流程}
查询检索子流程描述如下：
\begin{enumerate}
    \item \textbf{查询方式选择}：
    \begin{itemize}
        \item 用户可选择以下两种查询方式之一：
        \begin{itemize}
            \item \textbf{细胞编号查询}：从下拉列表或输入框中输入数据集中存在的细胞ID/索引号。
            \item \textbf{自定义向量查询}：手动输入或上传JSON格式的向量（维度需与数据集一致）。
        \end{itemize}
    \end{itemize}
    \item \textbf{检索参数设置}：
    \begin{itemize}
        \item \textbf{返回结果数量（k）}：用户指定需要返回的最相似细胞数量，默认值为10，范围为1-1000。
        \item \textbf{索引类型选择}：选择本次查询使用的索引（已构建的索引或线性扫描）。
        \item \textbf{距离度量方式}：支持欧氏距离、余弦相似度、内积等，用户可根据数据特点选择。
        \item \textbf{近似检索额外参数}：对于近似索引，可调整检索精度参数（如IVF的nprobe、HNSW的ef\_search），以平衡速度与精度。
        \item \textbf{是否对比精确检索}：勾选后系统同时执行线性扫描检索，用于计算召回率等评测指标。
    \end{itemize}
    \item \textbf{执行检索}：
    \begin{itemize}
        \item 用户点击“检索”按钮提交查询请求。
        \item 系统记录查询开始时间，根据所选索引类型和参数调用底层检索接口。
        \item 若为细胞编号查询，系统先从数据集中提取对应的向量；若为自定义向量查询，直接使用用户提供的向量。
        \item 检索执行完成后，系统记录查询结束时间，计算查询耗时。
        \item 若用户勾选了对比精确检索，系统同时执行线性扫描并计算召回率。
    \end{itemize}
    \item \textbf{结果返回}：
    \begin{itemize}
        \item 检索结果包含top-k个相似细胞的ID/索引号及其对应的距离/相似度得分。
        \item 系统将结果以JSON格式返回前端，同时存储本次查询记录（查询方式、参数、耗时、召回率等）至日志。
    \end{itemize}
    \item \textbf{异常处理}：
    \begin{itemize}
        \item 若用户输入的细胞编号不存在，系统提示“细胞编号不存在，请重新输入”。
        \item 若自定义向量维度与数据集不匹配，系统提示“向量维度错误，期望维度为X”。
        \item 若所选索引尚未构建，系统提示“请先构建索引”。
    \end{itemize}
\end{enumerate}

\subsubsection{可视化展示子流程}
可视化展示子流程描述如下：
\begin{enumerate}
    \item \textbf{结果数据接收}：
    \begin{itemize}
        \item 前端接收后端返回的检索结果JSON数据，包含相似细胞列表及其得分。
        \item 同时接收查询耗时、召回率等性能指标数据。
    \end{itemize}
    \item \textbf{表格展示}：
    \begin{itemize}
        \item 系统将top-k相似细胞以表格形式呈现，列包括：排名、细胞ID、距离/相似度得分。
        \item 表格支持排序、搜索和分页功能。
        \item 用户点击表格中的某一细胞，可查看该细胞的详细信息（如原始表达向量）。
    \end{itemize}
    \item \textbf{散点图可视化}：
    \begin{itemize}
        \item 系统预先计算或加载数据集的二维投影坐标（如t-SNE、UMAP或PCA结果）。
        \item 在散点图上用不同颜色和标记区分：查询细胞、相似结果细胞、其他细胞。
        \item 提供图例说明，鼠标悬停在点上可显示细胞ID和相似度得分。
        \item 支持缩放、平移等交互操作，方便用户观察细胞分布关系。
    \end{itemize}
    \item \textbf{性能评测面板}：
    \begin{itemize}
        \item 系统以仪表盘或卡片形式展示本次查询的评测指标：
        \begin{itemize}
            \item 查询耗时（毫秒）
            \item 召回率（若与精确检索对比）
            \item 精度@k（若与精确检索对比）
            \item 索引类型和参数
        \end{itemize}
        \item 提供历史查询记录对比功能，用户可查看不同参数配置下的性能差异。
    \end{itemize}
    \item \textbf{索引状态展示}：
    \begin{itemize}
        \item 在侧边栏或独立页面展示当前数据集的索引状态：
        \begin{itemize}
            \item 已构建的索引列表及参数
            \item 索引文件大小
            \item 构建时间
        \end{itemize}
        \item 用户可在此快速切换默认索引或删除索引。
    \end{itemize}
    \item \textbf{结果导出}：
    \begin{itemize}
        \item 用户可将检索结果导出为CSV或JSON文件，便于后续离线分析。
    \end{itemize}
\end{enumerate}

% ====================== 你提供的第4部分：数据需求（已放在正确位置） ======================
\section{数据需求}
数据需求是单细胞高维向量数据ANN检索系统进行数据库设计、数据存储规划、数据流管控与模块交互的核心依据，本章节全面梳理系统全业务流程所涉及的数据类型、流转规则、存储要求与标准化定义，保障系统数据的完整性、一致性、安全性与可追溯性，为后续系统开发与数据管理提供明确规范。

\subsection{数据需求描述}
本系统的核心数据围绕单细胞高维向量数据的导入、预处理、索引构建、检索查询、可视化展示与性能评测全流程产生，按照数据用途与业务属性划分为\textbf{基础业务数据}、\textbf{系统配置数据}、\textbf{操作日志数据}三大类别，各类数据的具体内容、存储要求与约束规则如下：

\subsubsection{基础业务数据}
基础业务数据是支撑系统核心检索功能的关键数据，直接服务于单细胞数据相似性检索业务，需严格保证数据的准确性、完整性、时效性与访问隔离性，具体包含四类核心数据：
\begin{enumerate}
    \item \textbf{单细胞原始/预处理数据}
    存储用户上传导入的单细胞“细胞×基因”表达矩阵原始数据，以及经系统标准化处理后的规整数据。核心内容包括细胞唯一编号、基因名称、基因表达量数值、样本来源信息；预处理后新增数据归一化、标准化、降维后的高维向量特征值。数据按用户维度严格隔离，不同用户的数据相互独立、不可越权访问，确保数据隐私与归属权。
    \item \textbf{索引数据}
    存储基于ANN算法构建完成的索引二进制文件与结构化元信息。元信息涵盖索引唯一ID、索引类型（HNSW/FAISS/Annoy等）、关联数据源ID、索引构建时间、构建参数配置、索引文件大小、运行状态（可用/未可用/构建中）、所属用户ID，实现索引的全生命周期管理与快速调用。
    \item \textbf{检索数据}
    记录用户每一次检索操作的全量信息，包括检索唯一ID、操作用户ID、关联索引ID、检索核心参数（检索类型、距离度量方式、top-k数值）、查询条件（细胞编号/自定义高维向量）、top-k相似细胞检索结果、检索总耗时、检索执行时间，为结果回溯、可视化展示与性能分析提供数据支撑。
    \item \textbf{性能评测数据}
    存储系统性能评测任务的全量数据，包含评测唯一ID、执行用户ID、关联索引与数据源ID、评测参数配置、多轮测试核心指标（单次检索耗时、召回率、精确率）、评测统计分析结果、评测生成时间，用于量化对比不同索引、不同参数下的检索效率与精度。
\end{enumerate}

\subsubsection{系统配置数据}
系统配置数据为系统稳定运行、权限管控、参数默认设置提供支撑，具备高稳定性与可配置性，支持管理员灵活调整与维护，具体包含三类数据：
\begin{enumerate}
    \item \textbf{用户信息数据}
    存储系统所有用户的账号与身份信息，包括用户唯一ID、登录账号名、加密存储密码、用户角色类型（普通用户/系统管理员）、个人基本信息（姓名、联系方式）、账号注册时间、当前登录状态，是系统身份认证与权限控制的基础。
    \item \textbf{系统参数配置数据}
    存储系统全局默认参数，涵盖数据预处理默认规则（缺失值填充方式、归一化/标准化方法）、索引构建默认参数（线程数、算法核心参数）、检索功能默认配置（距离度量方式、top-k默认值）、可视化展示样式参数，保障系统开箱即用，同时支持用户自定义调整。
    \item \textbf{数据格式配置数据}
    定义系统支持的单细胞数据标准格式、文件后缀名、数据解析规则，为数据上传后的格式校验、自动解析提供依据，确保流入系统的单细胞数据符合标准化要求。
\end{enumerate}

\subsubsection{操作日志数据}
操作日志数据用于系统运维监控、操作追溯与故障排查，具备不可篡改、连续记录、安全存储的特性，具体分为两类日志：
\begin{enumerate}
    \item \textbf{用户操作日志}
    全量记录用户在系统内的所有操作行为，包括日志唯一ID、操作用户ID、操作类型（注册、登录、数据导入、索引构建、检索、导出、删除等）、操作对象（数据ID/索引ID/检索ID）、操作执行时间、操作结果（成功/失败）、失败时的错误详情信息，实现用户操作可追溯。
    \item \textbf{系统运行日志}
    记录系统核心模块的运行状态与异常信息，包括日志唯一ID、日志级别（普通信息/警告/错误）、运行模块名称、日志具体内容、日志产生时间，便于管理员监控系统运行状态、快速定位故障问题。
\end{enumerate}

\subsection{数据流图}
本系统采用\textbf{分层数据流图（DFD）}设计，分为\textbf{0层（顶层）数据流图}与\textbf{1层（底层）数据流图}，清晰直观地展示数据在外部实体、系统功能模块、数据存储之间的输入、处理、存储与输出全流程，明确各模块的数据交互逻辑。

\subsubsection{0层数据流图}
0层数据流图聚焦系统整体数据交互框架，是对系统数据流转的宏观描述，核心要素定义如下：
\begin{itemize}
    \item \textbf{外部实体}：普通用户（科研人员）、系统管理员；
    \item \textbf{系统核心处理模块}：用户信息管理模块、数据管理模块、索引构建模块、查询检索模块、可视化展示模块、性能评测模块；
    \item \textbf{核心数据存储}：用户数据库、单细胞数据仓库、索引数据库、检索结果库、评测数据库、系统配置库、操作日志库；
    \item \textbf{核心数据流}：外部实体向系统模块发起数据输入（账号信息、数据文件、参数配置、查询指令）→系统模块对输入数据进行校验、处理、计算→处理后数据一部分流转至其他模块协同处理，一部分持久化存储至对应数据库→数据存储为系统模块提供数据读取支撑→系统模块将处理结果（检索结果、管理反馈、可视化数据）反馈至外部实体。
\end{itemize}

\subsubsection{1层数据流图}
1层数据流图对0层数据流图的核心业务模块进行拆解，细化模块内部的数据处理与流转细节，重点拆解两大核心模块：
\begin{enumerate}
    \item \textbf{数据管理模块数据流}
    普通用户→上传单细胞数据文件→格式校验模块（输入：原始数据文件；输出：格式校验结果/标准化数据）→数据预处理模块（输入：标准化数据；输出：归一化/降维后的规整数据）→单细胞数据仓库（持久化存储：预处理后核心数据）→结果反馈模块（输出：数据导入成功/失败提示）→普通用户。
    \item \textbf{查询检索模块数据流}
    普通用户→设置检索参数+输入查询条件→参数校验模块（输入：检索参数/查询条件；输出：参数合法性校验结果）→检索计算模块（输入：合法参数/查询条件、索引数据库加载的索引数据、单细胞数据仓库的目标数据；输出：top-k检索结果+检索耗时数据）→检索结果库（持久化存储：检索结果与性能数据）→结果反馈模块（输出：检索成功提示+可视化数据）→普通用户/可视化展示模块。
\end{enumerate}

\subsection{数据字典}
数据字典是对系统中所有数据项、数据结构、数据存储、数据流的标准化定义，明确数据名称、数据类型、长度、取值范围、关联模块与业务说明，为系统数据库设计、开发实现与数据管理提供统一规范，核心数据项定义如下：

\begin{table}[H]
\centering
\small
\caption{系统核心数据字典}
\begin{tabularx}{\linewidth}{p{1.2cm}p{1cm}p{0.8cm}p{1.8cm}p{2cm}X}
\toprule
数据项名称 & 数据类型 & 长度 & 取值范围 & 关联模块 & 说明 \\
\midrule
用户ID     & 字符串   & 32   & 全局唯一标识 & 所有模块 & 系统自动生成UUID，唯一标识每个用户 \\
细胞编号   & 字符串   & 20   & 自定义不可重复 & 数据管理、检索 & 细胞唯一标识，用户上传数据时定义 \\
基因维度   & 整数     & —    & ≥10 & 数据管理、索引构建 & 单细胞高维向量维度，即基因数量 \\
索引ID     & 字符串   & 32   & 全局唯一标识 & 索引构建、检索 & 唯一标识每个索引文件 \\
索引类型   & 字符串   & 10   & HNSW/FAISS/Annoy & 索引构建、检索 & 系统支持的ANN索引类型 \\
检索类型   & 字符串   & 6    & 精确/近似 & 检索、性能评测 & 系统支持的两种检索模式 \\
top-k值    & 整数     & —    & 1≤k≤100 & 检索、性能评测 & 相似细胞返回数量，默认10 \\
距离度量   & 字符串   & 12   & 欧氏距离/余弦相似度/曼哈顿距离 & 检索、性能评测 & 细胞相似性计算方式 \\
检索耗时   & 浮点数   & —    & ≥0 & 检索、性能评测 & 单位秒，保留3位小数 \\
召回率     & 浮点数   & —    & 0~1 & 性能评测 & 近似检索精度核心指标 \\
精确率     & 浮点数   & —    & 0~1 & 性能评测 & 检索结果有效性指标 \\
操作结果   & 字符串   & 4    & 成功/失败 & 操作日志 & 用户操作与系统运行结果 \\
数据格式   & 字符串   & 10   & h5ad/CSV/TSV & 数据管理 & 系统支持的单细胞数据格式 \\
索引状态   & 字符串   & 10   & 可用/未可用/构建中 & 索引构建 & 索引运行与加载状态 \\
\bottomrule
\end{tabularx}
\end{table}

% ===================== 5. 功能需求（已替换） =====================
\section{功能需求}
\subsection{功能划分}
为确保系统的高可维护性与可扩展性，本系统在整体架构上遵循高内聚、低耦合的模块化设计原则。围绕单细胞高维向量数据的导入、索引、检索及评估这一核心业务闭环，系统被按逻辑划分为\textbf{六大核心功能模块}。各模块各司其职，通过标准化接口进行数据交互与协同：
\begin{enumerate}[1.]
    \item \textbf{用户信息模块}：负责用户实体信息的全生命周期管理及访问权限的鉴权隔离；
    \item \textbf{数据管理模块}：构建系统数据源的准线，提供单细胞数据的规范化导入、校验与预处理流水线；
    \item \textbf{索引构建模块}：基于前沿ANN算法，实现高维向量索引的构建、多状态流转及生命周期维护；
    \item \textbf{查询检索模块}：承担系统的核心分析算力，依据用户定制参数执行精确及近似空间检索任务；
    \item \textbf{可视化展示模块}：打破数据屏障，通过丰富的多维交互图表直观投射检索结果及相似度分布特征；
    \item \textbf{性能评测模块}：提供自动化基准测试管线，量化系统检索的效率与准确率，输出高质量评测报告。
\end{enumerate}

\subsection{功能描述}
\subsubsection{用户信息模块}
作为系统安全与权限管理的基础屏障，该模块提供面向普通用户的访问前驱服务及面向管理员的后台运维服务。
\begin{itemize}
    \item \textbf{用户认证与授权}：不仅提供常规的账号注册、安全登录及密码找回功能，还引入基于Token的无状态会话管理（如JWT），确保跨终端访问的安全性。用户的密码等敏感信息采用加盐哈希（如bcrypt算法）进行单向加密存储，严防数据泄露。
    \item \textbf{基于角色的访问控制（RBAC）}：严格隔离普通用户与管理员的操作权限空间。普通用户被定配为数据使用者，仅受权对自有上传数据与所建索引进行读写；管理员拥有全局系统视野，具备跨用户的账号冻结、角色指派、数据审核及核心运行日志查阅权限。
    \item \textbf{操作留痕与审计}：系统底层内嵌审计拦截器，对所有用户的关键行为（如登录登出、提权、异常数据修改等）进行时序级日志留痕，用以满足后续的安全回溯与系统运维排查需求。
\end{itemize}

\subsubsection{数据管理模块}
该模块旨在建立并规范化系统的底层单细胞数据源，确保流入计算引擎的质量与格式的一致性。
\begin{itemize}
    \item \textbf{多模态数据摄取}：支持基于Web端的异步数据流式上传，高度包容诸如CSV、TSV及主流单细胞专用格式h5ad等，针对GB级别大文件采用分片断点续传策略以确保上传的稳定性与效率。
    \item \textbf{严苛的校验拦截}：在导入侧构建安全“防线”，自动应用Schema模式匹配技术拦截维度异常、无效字符、空稀疏度超标及缺失表头等非法类型数据，对不合规数据进行拦截并输出定位至行列的详明勘误报告。
    \item \textbf{预处理流水线}：针对单细胞表达矩阵所特有的离散性与噪声，提供高度弹性的清洗降噪支持。功能囊括多策略缺失值自动逼近（邻近均值/中位数/KNN推断）、基因数值归约标准化（如Log1p转换、Z-Score缩放/Min-Max规范化），以及为缓解维度灾难而可选配的线性降维（PCA）和非线性流形映射（t-SNE/UMAP）。
    \item \textbf{多实例租户隔离}：所有经由预处理脱水清洗后的规格化数据，在写入底层数据仓库时均绑定强约束的用户ID外键标识，施行物理隔离与访问确权。
\end{itemize}

\subsubsection{索引构建模块}
该模块通过高度自定的工业级ANN技术支撑系统的高频高维数据检索吞吐能力。
\begin{itemize}
    \item \textbf{多态ANN引擎支持}：允许用户依据特定的数据拓扑流型特性及具体的查准容忍度，精细化选型以构建检索索引。集成包括HNSW（基于导航小世界图，高召回率）、FAISS（基于倒排量化，支持密集型计算张量加速）及Annoy（基于随机投影森林，高度内存友好）在内的业界多极前沿算法框架。
    \item \textbf{超参数调优面板}：向高阶用户暴露算法隐层旋钮，例如HNSW算法中的连接分支束参数$M$及动态候选集搜索深度$ef\_construction$，以及并行的并发构建线程池规模调参。
    \item \textbf{热插拔生命周期管理}：在构建任务生成静态序列化索引切片后，系统对所有的索引文件实行细粒度的状态机调度（涵盖：未装载、加载中、就绪与损坏回收四态）。赋予用户对庞大索引执行一键按需唤醒（挂载至常驻内存）以及懒卸载（回收内存配额）的操纵特权，从而平衡服务器内存压力及检索极速响应耗时。
\end{itemize}

\subsubsection{查询检索模块}
查询检索模块承担了整个系统链路中最密集且高频的核心计算引擎角色，负责高效地在茫茫细胞海中寻觅高纯度相似样本。
\begin{itemize}
    \item \textbf{条件多态兼容}：检索入参的设计兼具普遍性与发散性支持。既允许用户利用体系内既有单细胞的ID作为锚点，也开放用户透传临时客制化的一维及批量的多维张量数据矩阵作为查询探针，同时模块内置张量尺度对其校验逻辑，规避不匹配引发的空指针或溢出异常。
    \item \textbf{双轨计算推流}：提供两条相互平行的计算轨道——追求极致精准的“暴力匹配（Brute-Force）”轨道（常用于Baseline基线构建）与具备高伸缩弹性的ANN“近似空间检索”轨道。
    \item \textbf{拓扑测度全家桶}：全面兼容并供选如极端的欧几里得距离（L2测度）、偏重方向相关的余弦夹角相似度及皮尔逊相关系数等多种传统数学距离评估模式以切合多元的基因序列研判需求。
    \item \textbf{池化结果缓存}：采用LRU等热点内存淘汰缓冲拦截机制。针对高频的相同检索阈值（如针对某一罕见细胞簇固定配置参数及Top-K数值发起的反复查询请求），系统跳过重复开销，对命中的Top-K极近样本及其排序列表作快速秒级重放。
\end{itemize}

\subsubsection{可视化展示模块}
将高维稀疏矩阵转化为可感知的业务洞察力，该模块主要负责打破多维结果产生的数据认知屏障。
\begin{itemize}
    \item \textbf{富态展示大屏}：模块基于ECharts或D3引擎渲染，除提供常规二维带有微观透视特性的检索表单（支持多维度混合排序与前端过滤）外，提供极强表现力的三维视效。例运用热力聚集网格挖掘组内相似度峰值靶点、利用带有基因标记漂浮提示的t-SNE散点群云图解构靶向细胞在三维特征空间的剥落与集聚聚类表征、通过双坐标轴复合折线图解析Top-K相似度的梯度跳崖式衰退态势。
    \item \textbf{深度下钻交互}：赋予图表强大的数据绑定响应力，支持对散点集群进行缩放（Zoom-in/out）、平移（Pan）与漫游悬停（Hovering），对于图表中敏感靶点单细胞可以直接点击穿越进入详细基因组表达特征图谱（如提供平行坐标系联动展示关键基因序列的波动情况）。
    \item \textbf{全模态档案留存}：实现图表级与数据汇集的“分离导出”，既可以输出SVG高清矢量矢量图形或高分辨率PNG图形供撰写权威科研Paper插图排版所用，又能将查询下钻取得的全量清洗清洗及运算相似度原始数据集通过CSV或Excel格式无保留导出分发。
\end{itemize}

\subsubsection{性能评测模块}
为对复杂、随机的在线模型执行可追溯、可审计的调优考察，建立并集成的一套内置的白盒基准测试靶场。
\begin{itemize}
    \item \textbf{用例发生器驱动}：允许测试规划者从测试面板框定数据抽样密度、索引实例及随机/靶态测试用例包。评测启动后，采用压力机发生器模拟真实高并发调用环境，向索引服务抛投随机探测张量并发集，进行模拟压力加载。
    \item \textbf{三大核心量化标尺}：以精细切片的粒度记录并审计算法硬性指标：实时演算召回率（Recall@K，用于评断ANN精度向全网精确最近邻匹配逼近的保真水平）、目标预测命中精确度（Precision）与瞬态查询延时开销（Query Latency, 涵盖P95/P99分位线响应开销等长尾指标测定）。
    \item \textbf{基准报告图册产出}：对多批次、不同调优版本参数或不同引擎核心执行同等规模实验后，形成对比矩阵分析，直接绘制包括ROC曲线或“吞吐-耗时（QPS vs Latency）”双限边界制图。并支持最终拼装成标准的实验分析电子白皮书文档提供给操作者作为最终性能定调指引。
\end{itemize}
\section{性能/非功能需求}

\subsection{准确性}
\begin{enumerate}[1.]
   \item 数据预处理的计算结果误差需控制在 1\% 以内，保证数据标准化质量；
   \item 精确检索的结果需 100\% 准确，与传统 KNN 算法计算结果完全一致；
   \item 近似检索的召回率需≥95\%（针对 10 万级细胞样本、top-10 检索）；
   \item 性能评测的指标计算误差需控制在 0.5\% 以内；
   \item 系统展示的所有数据需与数据库存储数据完全一致。
\end{enumerate}

\subsection{及时性}
\begin{enumerate}[1.]
   \item Web 端页面响应时间≤2 秒，无操作时页面加载时间≤3 秒；
   \item 数据格式校验响应时间≤5 秒（针对 10 万级细胞样本）；
   \item 数据预处理时间≤3 分钟（针对 10 万级、1000 维细胞样本）；
   \item ANN 索引构建时间≤10 分钟（针对 10 万级、1000 维细胞样本）；
   \item 近似检索响应时间≤1 秒，精确检索响应时间≤5 秒；
   \item 性能评测 10 轮测试总耗时≤正常检索耗时×15；
   \item 系统所有操作的结果反馈时间≤1 秒。
\end{enumerate}

\subsection{可扩充性}
\begin{enumerate}[1.]
   \item \textbf{功能可扩充}：支持后续新增更多 ANN 索引类型、距离度量方式和数据预处理方法；
   \item \textbf{数据可扩充}：支持后续增加超大规模细胞样本处理能力，并兼容更多数据格式；
   \item \textbf{性能可扩充}：支持通过增加服务器节点和优化算法提升检索效率；
   \item \textbf{用户可扩充}：支持大规模用户注册与管理，用户数量增加不会显著影响系统性能。
\end{enumerate}

\subsection{易用性}
\begin{enumerate}[1.]
   \item \textbf{界面设计}：Web 端界面简洁直观，功能入口清晰；
   \item \textbf{操作流程}：核心业务流程实现一站式操作，支持一键式操作；
   \item \textbf{提示信息}：所有操作提供清晰易懂的提示信息；
   \item \textbf{操作引导}：提供简易的新手引导或悬浮提示；
   \item \textbf{兼容性}：兼容主流浏览器和常规电脑屏幕分辨率。
\end{enumerate}

\subsection{易维护性}
\begin{enumerate}[1.]
   \item \textbf{代码规范}：遵循统一代码规范，保证可读性和可维护性；
   \item \textbf{模块化设计}：各功能模块独立，接口标准化；
   \item \textbf{数据管理}：数据按类型分类存储，支持备份和恢复；
   \item \textbf{日志管理}：记录详细的用户操作日志和系统运行日志；
   \item \textbf{配置管理}：核心参数采用配置文件集中管理。
\end{enumerate}

\subsection{标准性}
\begin{enumerate}[1.]
   \item \textbf{开发标准}：遵循软件工程通用开发标准；
   \item \textbf{数据标准}：单细胞数据预处理和存储遵循生物信息学领域通用标准；
   \item \textbf{接口标准}：模块间接口与前后端交互接口遵循 RESTful API 标准；
   \item \textbf{UML 标准}：系统设计过程中的 UML 图绘制遵循官方标准；
   \item \textbf{文档标准}：所有文档遵循统一的文档规范。
\end{enumerate}

\subsection{先进性}
\begin{enumerate}[1.]
   \item \textbf{技术先进性}：采用主流 ANN 检索算法和 Web 开发技术栈；
   \item \textbf{功能先进性}：整合数据预处理、索引构建、检索、可视化和性能评测于一体；
   \item \textbf{设计先进性}：采用模块化、分层化设计，支持分布式计算和后续扩展。
\end{enumerate}

\subsection{安全性}
\begin{enumerate}[1.]
   \item \textbf{用户信息安全}：密码采用加密算法存储，并支持登录超时自动退出；
   \item \textbf{数据安全}：不同用户的数据隔离存储，普通用户仅可访问自身数据；
   \item \textbf{操作安全}：核心操作增加二次确认机制，管理员操作记录详细日志；
   \item \textbf{系统安全}：防止 SQL 注入、XSS 和 CSRF 等常见攻击。
\end{enumerate}

\subsection{可靠性}
\begin{enumerate}[1.]
   \item \textbf{系统稳定性}：系统支持 7×24 小时不间断运行，多用户并发操作时性能无显著下降；
   \item \textbf{容错性}：对非法操作具有容错能力，不会因非法输入导致系统崩溃；
   \item \textbf{恢复性}：系统故障后可快速恢复，已存储数据不会丢失。
\end{enumerate}

\section{系统运行要求}

\subsection{硬件配置要求}

\subsubsection{服务器端硬件配置}
\begin{table}[htbp]
\centering
\small
\begin{tabularx}{\linewidth}{p{2.2cm}p{2.2cm}p{2.6cm}L}
\toprule
硬件组件 & 最低配置 & 推荐配置 & 说明 \\
\midrule
CPU & 8 核 16 线程 & 16 核 32 线程 & 支撑高维向量计算、索引构建和检索，多核可提升并行处理效率 \\
内存 & 64GB & 128GB 及以上 & 存储大规模单细胞数据和索引文件，减少磁盘 IO \\
硬盘 & 1TB SSD & 2TB 及以上 SSD & 存储数据、索引文件和数据库数据 \\
网卡 & 千兆网卡 & 万兆网卡 & 保证服务器与客户端之间的网络传输速度 \\
显卡 & 10GB 及以上显存 GPU & 24GB 及以上显存 GPU & 可选，支持 GPU 加速的索引构建和检索算法 \\
\bottomrule
\end{tabularx}
\end{table}

\subsubsection{客户端（用户端）硬件配置}
\begin{table}[htbp]
\centering
\small
\begin{tabularx}{\linewidth}{p{2.2cm}p{2.2cm}p{2.6cm}L}
\toprule
硬件组件 & 最低配置 & 推荐配置 & 说明 \\
\midrule
CPU & 4 核 8 线程 & 8 核 16 线程 & 满足 Web 端页面渲染和简单的本地数据处理 \\
内存 & 8GB & 16GB & 保证浏览器流畅运行 \\
硬盘 & 100GB 可用空间 & 200GB 及以上可用空间 & 存储本地单细胞数据文件和导出结果 \\
网卡 & 百兆网卡 & 千兆网卡 & 保证数据上传和页面访问速度 \\
显示器 & 1366×768 分辨率 & 1920×1080 及以上分辨率 & 保证可视化结果清晰展示 \\
\bottomrule
\end{tabularx}
\end{table}

\subsection{软件配置要求}

\subsubsection{服务器端软件配置}
\begin{table}[htbp]
\centering
\small
\begin{tabularx}{\linewidth}{p{3cm}p{4.2cm}L}
\toprule
软件类型 & 推荐软件/版本 & 说明 \\
\midrule
操作系统 & Linux CentOS 7/8、Ubuntu 20.04/22.04 & 稳定、安全，适合服务器部署 \\
Web 服务器 & Nginx 1.20+、Apache 2.4+ & 提供 Web 端访问服务 \\
应用服务器 & Tomcat 9.0+、uWSGI 2.0+ & 运行后端应用程序 \\
数据库管理系统 & MySQL 8.0+、PostgreSQL 14+ & 存储用户信息、系统配置、操作日志等结构化数据 \\
数据仓库 & HDFS、MongoDB & 可选，存储大规模的单细胞非结构化/半结构化数据 \\
Python 环境 & Python 3.8+ & 运行数据预处理、索引构建、检索、评测核心算法 \\
Java 环境 & JDK 1.8+/11+ & 若后端采用 Java 开发，需配置对应的 JDK 环境 \\
容器化技术 & Docker 20.10+、K8s 1.20+ & 可选，实现系统容器化部署和管理 \\
\bottomrule
\end{tabularx}
\end{table}

\subsubsection{客户端（用户端）软件配置}
\begin{table}[htbp]
\centering
\small
\begin{tabularx}{\linewidth}{p{3cm}p{4.2cm}L}
\toprule
软件类型 & 推荐软件/版本 & 说明 \\
\midrule
操作系统 & Windows 10/11、macOS 12+、Linux Ubuntu 20.04+ & 兼容主流桌面操作系统 \\
浏览器 & Chrome 90+、Firefox 88+、Edge 90+ & 支持 Web 端的所有功能 \\
办公软件 & Microsoft Office 2019+、WPS 2021+ & 打开和编辑导出的结果、评测报告 \\
解压缩软件 & WinRAR、7-Zip & 解压单细胞数据文件和索引文件 \\
\bottomrule
\end{tabularx}
\end{table}

\subsubsection{系统开发技术栈要求}
\begin{enumerate}[1.]
   \item \textbf{前端开发}：采用 Vue3.x/React18.x 作为核心框架，Element Plus/Ant Design 作为 UI 组件库，ECharts/Plotly 作为可视化库；
   \item \textbf{后端开发}：支持 Python（FastAPI/Django）或 Java（SpringBoot/SpringCloud）开发；
   \item \textbf{算法开发}：基于 Python 的开源库（FAISS、scikit-learn、Annoy、PyTorch）实现预处理、索引构建、检索和评测；
   \item \textbf{数据库开发}：采用 MySQL/PostgreSQL 存储结构化数据，采用 Redis 实现缓存，提升系统性能。
\end{enumerate}

\subsection{网络运行要求}
\begin{enumerate}[1.]
   \item 服务器端需接入稳定的局域网或互联网，网络带宽≥100Mbps；
   \item 客户端（用户端）的网络带宽≥10Mbps；
   \item 系统运行的网络环境需保证低延迟（≤50ms）、低丢包率（≤0.1\%）。
\end{enumerate}
\section{UML图}
\begin{figure}[H]
    \centering
\includegraphics[width=0.20 \linewidth]{单细胞高维向量数据ANN检索系统总业务流程.png}
    \caption{单细胞高维向量数据ANN检索系统总业务流程}
    \label{fig:ann_workflow}
\end{figure}
\end{document}