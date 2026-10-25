import streamlit as st
import csv
import os
import json
import subprocess
import requests
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# ================= 配置区 =================
EXE_PATH = r"C:\Users\30768\source\repos\VectorDB\x64\Debug\VectorDB.exe"
EXE_DIR = r"C:\Users\30768\source\repos\VectorDB\VectorDB" 
ADMIN_PASSWORD = "admin888" 

st.set_page_config(page_title="全本地 RAG", page_icon="🧠", layout="wide")
st.title("🧠 纯本地化 RAG (C语言并发 + 本地向量)")

@st.cache_resource
def load_embedding_model():
    # 使用国内的镜像下载（更快）
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    return SentenceTransformer('BAAI/bge-small-zh-v1.5')

model = load_embedding_model()

def get_local_embedding(text):
    return model.encode(text).tolist()

def generate_answer(context, question):
    # 调本地 Ollama
    prompt = f"你是一个智能助手。请根据以下资料回答问题，不要编造：\n【资料】：\n{context}\n\n【问题】：\n{question}"
    data = {"model": "qwen2.5:3b", "prompt": prompt, "stream": False, "options": {"num_thread": 8}}
    try:
        response = requests.post("http://127.0.0.1:11434/api/generate", json=data, timeout=300)
        return response.json().get("response", "模型没有返回内容。")
    except Exception as e:
        return f"本地大模型请求失败: {e}。请确保 Ollama 正在后台运行。"

# ================= 侧边栏 =================
with st.sidebar:
    st.header("📂 知识库管理 (管理员)")
    pwd = st.text_input("输入管理员密码解锁上传", type="password")
    
    if pwd == ADMIN_PASSWORD:
        st.success("✅ 管理员验证通过")
        uploaded_file = st.file_uploader("上传 PDF (支持大文件流式处理)", type="pdf")
        
        if st.button("🚀 解析并追加"):
            if uploaded_file is not None:
                with st.spinner("流式解析 PDF 中..."):
                    reader = PdfReader(uploaded_file)
                    chunks = []
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            for i in range(0, len(text), 500):
                                chunks.append(text[i:i+500])
                    
                    limit = min(len(chunks), 300) 
                    st.info(f"共提取 {len(chunks)} 块，本次处理前 {limit} 块。")
                    
                    vectors_path = os.path.join(EXE_DIR, 'vectors.csv')
                    chunks_path = os.path.join(EXE_DIR, 'chunks.json')
                    
                    chunk_map = {}
                    current_max_id = 0
                    if os.path.exists(chunks_path):
                        with open(chunks_path, "r", encoding='utf-8') as f:
                            chunk_map = json.load(f)
                            if chunk_map: current_max_id = max([int(k) for k in chunk_map.keys()])

                    progress = st.progress(0)
                    with open(vectors_path, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        for i, chunk in enumerate(chunks[:limit]):
                            vec = get_local_embedding(chunk)
                            if vec:
                                new_id = current_max_id + i + 1
                                writer.writerow([new_id] + vec)
                                chunk_map[str(new_id)] = chunk
                            progress.progress((i + 1) / limit)
                    
                    with open(chunks_path, "w", encoding='utf-8') as f:
                        json.dump(chunk_map, f, ensure_ascii=False)
                st.success(f"🎉 建库完成！当前总片段数: {len(chunk_map)}")
            else:
                st.warning("请先上传文件！")
    else:
        if pwd != "": st.error("密码错误！")
        st.info("当前为访客模式。可直接提问。")

# ================= 主聊天界面 =================
if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("请输入你的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("1. 向量化问题..."):
            q_vec = get_local_embedding(prompt)
        
        if q_vec:
            with st.spinner("2. 本地 C 语言并发检索..."):
                with open(os.path.join(EXE_DIR, 'query.csv'), 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([0] + q_vec)

                try:
                    result = subprocess.run([EXE_PATH], capture_output=True, text=True, cwd=EXE_DIR)
                    ids_str = result.stdout.strip().split()
                    perf_report = result.stderr.strip()

                    context = ""
                    chunks_path = os.path.join(EXE_DIR, "chunks.json")
                    if os.path.exists(chunks_path):
                        with open(chunks_path, "r", encoding='utf-8') as f:
                            chunk_map = json.load(f)
                        for idx in ids_str:
                            if idx in chunk_map:
                                context += chunk_map[idx] + "\n"

                    with st.expander("🔍 C 语言性能报告与检索原文"):
                        st.code(perf_report)
                        st.write(context)

                    with st.spinner("3. 大模型生成回答..."):
                        ans = generate_answer(context, prompt)
                        st.markdown(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                except Exception as e:
                    st.error(f"本地 C 语言调用失败: {e}")