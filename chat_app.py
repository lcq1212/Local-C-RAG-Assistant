import requests
import csv
import subprocess
import os

# ⚠️ 这里填你真实的智谱 API Key！千万不能有中文，保留两边的双引号
API_KEY = "efa2cc57d8664740bb409bda8d127d5e.pWrWiWFOa6zuvMVY" 

# 接口地址
EMBEDDING_URL = "https://open.bigmodel.cn/api/paas/v4/embeddings"
CHAT_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# C 程序路径和工作目录
EXE_PATH = r"C:\Users\30768\source\repos\VectorDB\x64\Debug\VectorDB.exe"
EXE_DIR = r"C:\Users\30768\source\repos\VectorDB\VectorDB" 

# 你的知识库
knowledge_base = [
    "计算机考研复试主要考察机试和面试。",
    "C语言是一门底层语言，需要手动管理内存。",
    "向量数据库可以通过计算余弦相似度来检索。",
    "苹果手机是市场上很受欢迎的电子产品。",
    "Python非常适合用来写爬虫和处理数据。"
]

# 1. 把文字变成向量 (Embedding)
def get_embedding(text):
    # 强制指定 utf-8 编码，防止报错
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }
    data = {"model": "embedding-2", "input": text}
    
    try:
        response = requests.post(EMBEDDING_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
    except Exception as e:
        print(f"\n❌ 获取向量失败: {e}")
        if response is not None:
            print(f"服务器返回: {response.text}")
        return None

# 2. 让大模型根据资料生成回答 (Generation)
def generate_answer(context, question):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    prompt = f"""你是一个智能问答助手。请根据以下参考资料回答用户的问题。
如果参考资料中找不到答案，请直接回答“根据现有资料，我无法回答这个问题”，不要编造。

【参考资料】：
{context}

【用户问题】：
{question}
"""
    data = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    print("🧠 正在让大模型总结答案...")
    try:
        response = requests.post(CHAT_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"\n❌ 生成回答失败: {e}")
        if response is not None:
            print(f"服务器返回: {response.text}")
        return "生成失败，请检查网络或API配置。"

# 3. 主流程
def main():
    print("=========================================")
    print("🤖 欢迎使用 完整版 RAG 智能问答助手！")
    print("=========================================")
    
    while True:
        user_input = input("\n请输入你的问题 (输入 q 退出): ")
        if user_input.lower() == 'q':
            break
        
        print("1️⃣ 正在将你的问题转化为向量...")
        query_vec = get_embedding(user_input)
        if not query_vec:
            continue

        # 写入 query.csv，交给 C 语言程序
        with open(os.path.join(EXE_DIR, 'query.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([0] + query_vec)

        print("2️⃣ 正在调用 C 语言底层进行极速检索...")
        # 运行 C 程序
        result = subprocess.run([EXE_PATH], capture_output=True, text=True, cwd=EXE_DIR)
        
        try:
            # 解析 C 程序返回的 Top 3 ID
            ids_str = result.stdout.strip().split()
            if not ids_str:
                print("❌ C 程序没有返回结果，请检查 Debug 文件夹下是否有 vectors.csv")
                continue
                
            matched_texts = []
            for id_str in ids_str:
                best_id = int(id_str)
                matched_texts.append(knowledge_base[best_id - 1])
            
            # 拼装上下文
            context = "\n".join(matched_texts)
            print(f"\n🔍 C语言检索到的底层资料：\n{context}")
            
            # 生成回答
            print("\n3️⃣ 正在调用大模型生成最终回答...")
            final_answer = generate_answer(context, user_input)
            
            print("\n================ 最终回答 ================")
            print(final_answer)
            print("==========================================")
                
        except Exception as e:
            print(f"❌ 系统解析失败: {e}")
            print(f"C语言原始输出: {result.stdout}")

if __name__ == "__main__":
    main()