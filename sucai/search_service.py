# -*- coding: utf-8 -*-
"""
《长生界》风格素材检索服务（Embedding + Qdrant 封装）

启动后常驻内存，暴露 HTTP 接口，供写作 Skill 调用。
写作 Skill 无需加载模型，只需发送文本查询即可。

启动:
    python embedding_service.py

接口:
    POST /search
    Body: {"query": "写战斗", "top_k": 5, "type_filter": "combat", "mood_filter": null}
    
    POST /embed
    Body: {"text": "写战斗"}
    
    GET /health
    返回服务状态
"""

import json
import time
from typing import List, Dict, Optional

from flask import Flask, request, jsonify

# ==================== 配置 ====================

QDRANT_HOST = "http://123.56.245.73:6333"
QDRANT_COLLECTION = "changshengjie_corpus"
EMBEDDING_MODEL = "BAAI/bge-m3"
PORT = 5000

# ==================== 全局单例（启动时加载一次）====================

print("[服务启动] 加载 BGE-M3 模型...")
import os
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

model = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=True)
qdrant = QdrantClient(QDRANT_HOST)
print(f"[服务启动] 模型就绪 | 设备: {model.device}")
print(f"[服务启动] Qdrant 连接: {QDRANT_HOST} | Collection: {QDRANT_COLLECTION}")

app = Flask(__name__)


# ==================== 核心函数 ====================

def do_search(
    query: str,
    top_k: int = 5,
    type_filter: Optional[str] = None,
    mood_filter: Optional[str] = None,
    min_score: float = 0.0
) -> List[Dict]:
    """
    执行完整检索：文本 → Embedding → Qdrant → 结果
    """
    # 1. 编码
    t0 = time.time()
    query_vec = model.encode(query, normalize_embeddings=True, convert_to_numpy=True).tolist()
    encode_ms = round((time.time() - t0) * 1000, 2)
    
    # 2. 过滤条件
    must_conditions = []
    if type_filter:
        must_conditions.append(FieldCondition(key="type", match=MatchValue(value=type_filter)))
    if mood_filter:
        must_conditions.append(FieldCondition(key="mood", match=MatchValue(value=mood_filter)))
    search_filter = Filter(must=must_conditions) if must_conditions else None
    
    # 3. 检索
    t0 = time.time()
    results = qdrant.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vec,
        limit=top_k,
        query_filter=search_filter,
        with_payload=True,
        score_threshold=min_score if min_score > 0 else None
    ).points
    search_ms = round((time.time() - t0) * 1000, 2)
    
    # 4. 格式化
    output = []
    for r in results:
        p = r.payload
        output.append({
            "score": round(r.score, 4),
            "text": p.get("text", ""),
            "type": p.get("type", ""),
            "mood": p.get("mood", ""),
            "writing_technique": p.get("writing_technique", ""),
            "reference_for": p.get("reference_for", ""),
            "characters": p.get("characters", []),
            "keywords": p.get("keywords", []),
            "chapter": p.get("chapter", ""),
        })
    
    return output, encode_ms, search_ms


# ==================== HTTP 接口 ====================

@app.route("/health", methods=["GET"])
def health():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "model": EMBEDDING_MODEL,
        "device": str(model.device),
        "collection": QDRANT_COLLECTION,
    })


@app.route("/embed", methods=["POST"])
def embed():
    """
    只返回文本的 Embedding 向量
    Body: {"text": "写战斗"}
    """
    data = request.get_json(force=True)
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "text is required"}), 400
    
    vec = model.encode(text, normalize_embeddings=True, convert_to_numpy=True).tolist()
    return jsonify({"vector": vec, "text": text})


@app.route("/search", methods=["POST"])
def search():
    """
    完整检索：文本 → Embedding → Qdrant → 返回结果
    Body: {"query": "写战斗", "top_k": 5, "type_filter": "combat", "mood_filter": null}
    """
    data = request.get_json(force=True)
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "query is required"}), 400
    
    top_k = min(int(data.get("top_k", 5)), 20)  # 上限20条
    type_filter = data.get("type_filter")
    mood_filter = data.get("mood_filter")
    min_score = float(data.get("min_score", 0.0))
    
    try:
        results, encode_ms, search_ms = do_search(
            query=query,
            top_k=top_k,
            type_filter=type_filter,
            mood_filter=mood_filter,
            min_score=min_score
        )
        return jsonify({
            "query": query,
            "results": results,
            "count": len(results),
            "timing_ms": {"encode": encode_ms, "search": search_ms}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== 启动 ====================

if __name__ == "__main__":
    print(f"[服务启动] 监听 http://0.0.0.0:{PORT}")
    print(f"[服务启动] 测试: curl -X POST http://localhost:{PORT}/search -H 'Content-Type: application/json' -d '{{\"query\":\"写战斗\"}}'")
    # threaded=True 允许多并发请求
    app.run(host="0.0.0.0", port=PORT, threaded=True)
