from flask import Flask, request, jsonify
import csv
import subprocess
import os
import json

app = Flask(__name__)
EXE_PATH = r"C:\Users\30768\source\repos\VectorDB\x64\Debug\VectorDB.exe"
EXE_DIR = r"C:\Users\30768\source\repos\VectorDB\VectorDB" 
SECRET_TOKEN = "my_super_secret_token_123"

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    if data.get("token") != SECRET_TOKEN: return jsonify({"error": "Unauthorized"}), 401
    query_vec = data.get("vector")
    if not query_vec: return jsonify({"error": "No vector provided"}), 400

    with open(os.path.join(EXE_DIR, 'query.csv'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([0] + query_vec)

    try:
        result = subprocess.run([EXE_PATH], capture_output=True, text=True, cwd=EXE_DIR)
        ids = [int(i) for i in result.stdout.strip().split()]
        perf_report = result.stderr.strip()

        matched_texts = []
        chunks_path = os.path.join(EXE_DIR, "chunks.json")
        if os.path.exists(chunks_path):
            with open(chunks_path, "r", encoding='utf-8') as f:
                chunk_map = json.load(f)
            for idx in ids:
                if str(idx) in chunk_map:
                    matched_texts.append(chunk_map[str(idx)])

        return jsonify({"ids": ids, "texts": matched_texts, "performance": perf_report})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 本地 C 语言算力节点已启动！等待云端呼叫...")
    app.run(host='0.0.0.0', port=5000)