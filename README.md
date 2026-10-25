# 🧠 纯本地化 RAG 知识库问答系统

这是一个完全离线、零 API 费用的本地知识库问答系统。用户上传 PDF 后，系统通过本地开源模型进行向量化，并利用 C 语言手写的并发搜索引擎进行极速检索，最后通过本地部署的 LLM 生成回答。

## ✨ 核心亮点

*   **底层自研**：使用 C 语言从零手写高维向量 KNN 检索算法，结合 OpenMP 实现多线程并发，百万级数据检索仅需毫秒级。
*   **纯血本地化**：使用 `BAAI/bge-small-zh` 进行本地向量化，使用 `Ollama` (Qwen2.5) 进行本地生成，**断网也能完美运行**，杜绝任何隐私泄露与 API 费用。
*   **流式解析**：支持 500MB 级超大 PDF 文件的流式提取与分块，防止内存溢出。
*   **现代化前端**：使用 `Streamlit` 构建交互式 Web 界面，支持流式对话与检索证据可解释（可查看 C 语言性能报告）。

## 🛠️ 技术栈
*   **核心算法**: C / OpenMP
*   **接口与前端**: Python / Streamlit / pypdf
*   **AI 模型**: Sentence-Transformers (BGE 向量) / Ollama (Qwen2.5)
*   **通信**: 跨语言进程通信 (subprocess)

## 🚀 快速开始

1. 安装 Python 依赖: `pip install -r requirements.txt`
2. 确保本地已安装并运行 [Ollama](https://ollama.com/)，并拉取模型: `ollama run qwen2.5:3b`
3. 编译 C 代码 (`main.c`) 生成 `VectorDB.exe`。
4. 双击运行 `一键启动.bat` 或执行 `streamlit run web_app.py`。
5. 在网页左侧输入密码 `admin888`，上传 PDF 即可开始体验。

## 📸 界面截图
*(在这里放上你刚才那张绝美的 Streamlit 网页截图)*