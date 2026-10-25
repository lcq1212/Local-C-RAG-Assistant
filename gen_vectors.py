import requests
import csv

# ⚠️ 第一步：把下面引号里的文字，替换成你刚才在智谱复制的完整 API Key
API_KEY = "efa2cc57d8664740bb409bda8d127d5e.pWrWiWFOa6zuvMVY"

texts = [
    "计算机考研复试主要考察机试和面试。",
    "C语言是一门底层语言，需要手动管理内存。",
    "向量数据库可以通过计算余弦相似度来检索。",
    "苹果手机是市场上很受欢迎的电子产品。",
    "Python非常适合用来写爬虫和处理数据。"
]

vectors = []

print("开始向智谱 AI 请求真实向量...")

for i, text in enumerate(texts):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "embedding-2",
        "input": text
    }
    
    # 发送网络请求给智谱
    response = requests.post("https://open.bigmodel.cn/api/paas/v4/embeddings", headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        # 提取真实的 1024 维向量
        vector = result["data"][0]["embedding"] 
        vectors.append(vector)
        print(f"[{i+1}/5] 成功获取向量，维度：{len(vector)}")
    else:
        print(f"[{i+1}/5] 请求失败，错误信息：{response.text}")

# 把获取到的真实向量存进 CSV
if vectors:
    with open('vectors.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for i, vec in enumerate(vectors):
            # 写入格式：ID, 维度1, 维度2, ... 维度1024
            writer.writerow([i + 1] + vec)
    print("\n✅ 成功生成包含真实 AI 语义的 vectors.csv！")