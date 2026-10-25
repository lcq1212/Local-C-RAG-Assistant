import streamlit as st
import requests
import csv
import os
import json
from pypdf import PdfReader

# ================= 配置区 =================
# ⚠️ 安全提示：你的 API Key 暴露了！用完记得去智谱后台删掉旧的重新生成一个。
API_KEY=st.secrets.get("API_KEY","efa2cc57d8664740bb409bda8d127d5e.pWrWiWFOa6zuvMVY") 
EMBEDDING_URL = "https://open.bigmodel.cn/api/paas/v4/embeddings"
CHAT_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# ⚠️⚠️⚠️ 注意：如果 cpolar 重启了，必须把这里换成最新的 5000 端口地址TUNNEL_URL=st.secrets.get("TUNNEL_URL","https://147388c1.r31.cpolar.top/api/search")
SECRET_TOKEN = "my_super_secret_token_123"
EXE_DIR = r"C:\Users\30768\source\repos\VectorDB\VectorDB" 
ADMIN_PASSWORD = "admin888" 

st.set_page_config(page_title="分布式 RAG", page_icon="🌐", layout="wide")
st.title("🌐 分布式 RAG (本地算力 + 云端展示)")

# ================= 核心函数 =================
def get_embedding(text):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json; charset=utf-8"}
    data = {"model": "embedding-2", "input": text}
    try:
        response = requests.post(EMBEDDING_URL, headers=headers, json=data, timeout=10)
        return response.json()["data"][0]["embedding"]
    except:
        return None

def generate_answer(context, question):
    prompt = f"你是一个智能助手。请根据以下资料回答问题，不要编造：\n【资料】：\n{context}\n\n【问题】：\n{question}"
    data = {
        "model": "qwen2.5:3b",  # 👈 还原回 3b 模型
        "prompt": prompt,
        "stream": False,
        "options": {
            # 👈 删掉了 num_gpu: 0，现在它会让你的 GTX 1060 尽情咆哮！
            "num_thread": 8 
        }
    }
    try:
        # 显卡加速后速度会快很多，但为了防万一还是给个 120 秒超时
        response = requests.post("http://127.0.0.1:11434/api/generate", json=data, timeout=120)
        return response.json().get("response", "模型没有返回内容。")
    except Exception as e:
        return f"本地大模型请求失败: {e}。请确保 Ollama 正在后台运行，且显卡未崩溃。"

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
                    
                    limit = min(len(chunks), 300) # 一次最多300块防限流
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
                            vec = get_embedding(chunk)
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

# ================= 聊天区 =================
if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("请输入你的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("1. 向量化问题..."):
            q_vec = get_embedding(prompt)
        
        if q_vec:
            with st.spinner("2. 公网呼叫本地 C 语言算力..."):
                try:
                    payload = {"token": SECRET_TOKEN, "vector": q_vec}
                    res = requests.post(TUNNEL_URL, json=payload, timeout=15)
                    
                    if res.status_code == 200:
                        res_data = res.json()
                        context = "\n".join(res_data.get("texts", []))
                        
                        with st.expander("🔍 检索详情"):
                            st.code(res_data.get("performance", ""))
                            st.write(context)
                            
                        with st.spinner("3. 本地显卡狂飙总结中..."):
                            ans = generate_answer(context, prompt)
                            st.markdown(ans)
                        st.session_state.messages.append({"role": "assistant", "content": ans})
                    else:
                        st.error(f"后端报错: {res.text}")
                except Exception as e:
                    st.error("无法连接本地电脑！请确保 local_server.py 和 cpolar 正在运行，且 TUNNEL_URL 填写正确。")