# -*- coding: utf-8 -*-
"""
sucai 客户端脚本
===============
供写作 Skill 调用，封装了对 sucai 检索服务的 HTTP 请求。
客户端零依赖（仅用 Python 标准库），无需加载模型。

两种使用方式：
  1. Python 模块导入：
     from sucai.sucai_client import search, health
     results = search("写战斗场景", top_k=5)

  2. 命令行调用（供 Skill 脚本使用）：
     python sucai/sucai_client.py --query "写战斗" --top_k 5
     python sucai/sucai_client.py --health
"""

import json
import sys
import urllib.request
import urllib.error
import os

# ==================== 配置 ====================

# 从环境变量读取，或使用默认值
SUCAI_HOST = os.environ.get("SUCAI_HOST", "http://127.0.0.1:5000")
DEFAULT_TOP_K = 5
TIMEOUT_SECONDS = 30


# ==================== 核心 API ====================

def _post(endpoint: str, data: dict) -> dict:
    """内部 POST 请求封装"""
    url = f"{SUCAI_HOST.rstrip('/')}{endpoint}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body}"}
    except urllib.error.URLError as e:
        return {"error": f"连接失败: {e.reason}"}
    except json.JSONDecodeError:
        return {"error": "响应解析失败，非 JSON 格式"}


def _get(endpoint: str) -> dict:
    """内部 GET 请求封装"""
    url = f"{SUCAI_HOST.rstrip('/')}{endpoint}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body}"}
    except urllib.error.URLError as e:
        return {"error": f"连接失败: {e.reason}"}
    except json.JSONDecodeError:
        return {"error": "响应解析失败，非 JSON 格式"}


def health() -> dict:
    """
    检查服务健康状态。
    
    Returns:
        dict: {"status": "ok", "model": "...", "device": "...", ...}
        若服务不可达，返回 {"error": "..."}
    """
    return _get("/health")


def search(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    type_filter: str = None,
    mood_filter: str = None,
    min_score: float = 0.0,
) -> dict:
    """
    向量检索：文本 → Embedding → Qdrant → 结果。

    Args:
        query:       检索查询文本（如 "写战斗场景" "写情感对白"）
        top_k:       返回结果数量，默认 5，上限 20
        type_filter: 素材类型过滤（如 "combat" "dialogue" "description"）
        mood_filter: 情绪过滤（如 "tense" "sad" "exciting"）
        min_score:   最低相似度阈值（0.0 ~ 1.0）

    Returns:
        dict: {
            "query": "写战斗场景",
            "results": [
                {
                    "score": 0.8765,
                    "text": "片段正文...",
                    "type": "combat",
                    "mood": "tense",
                    "writing_technique": "动作描写",
                    "reference_for": "战斗节奏",
                    "characters": ["萧晨"],
                    "keywords": ["拳意", "杀意", "虚空"],
                    "chapter": "第3章",
                },
                ...
            ],
            "count": 5,
            "timing_ms": {"encode": 45.2, "search": 12.3}
        }
        若出错，返回 {"error": "..."}
    """
    body = {"query": query, "top_k": min(top_k, 20), "min_score": min_score}
    if type_filter:
        body["type_filter"] = type_filter
    if mood_filter:
        body["mood_filter"] = mood_filter
    return _post("/search", body)


def embed(text: str) -> dict:
    """
    获取文本的 Embedding 向量。

    Args:
        text: 待编码文本

    Returns:
        dict: {"vector": [...], "text": "..."}
        若出错，返回 {"error": "..."}
    """
    return _post("/embed", {"text": text})


# ==================== 命令行入口 ====================

def _format_results(data: dict) -> str:
    """格式化检索结果为可读文本"""
    if "error" in data:
        return f"[错误] {data['error']}"

    lines = [f"查询: {data.get('query', '')}"]
    lines.append(f"结果数: {data.get('count', 0)}")
    timing = data.get("timing_ms", {})
    if timing:
        lines.append(f"耗时: 编码 {timing.get('encode', 0)}ms / 检索 {timing.get('search', 0)}ms")
    lines.append("-" * 60)

    for i, r in enumerate(data.get("results", []), 1):
        lines.append(f"\n[{i}] 相似度: {r.get('score', 0):.4f}  |  类型: {r.get('type', '-')}  |  情绪: {r.get('mood', '-')}")
        lines.append(f"    手法: {r.get('writing_technique', '-')}")
        lines.append(f"    参考: {r.get('reference_for', '-')}")
        lines.append(f"    角色: {', '.join(r.get('characters', []))}")
        lines.append(f"    章节: {r.get('chapter', '-')}")
        lines.append(f"    文本: {r.get('text', '')[:200]}...")

    return "\n".join(lines)


def main():
    global SUCAI_HOST  # 须在函数体最前声明，否则 parser 中的引用报 SyntaxError
    import argparse

    parser = argparse.ArgumentParser(
        description="sucai 素材检索客户端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python sucai_client.py --query "写战斗场景" --top_k 5
  python sucai_client.py --query "情感对白" --type_filter dialogue --mood_filter sad
  python sucai_client.py --health
  python sucai_client.py --embed "测试文本"
        """,
    )
    parser.add_argument("--query", "-q", type=str, help="检索查询文本")
    parser.add_argument("--top_k", "-k", type=int, default=DEFAULT_TOP_K, help=f"返回结果数 (默认 {DEFAULT_TOP_K})")
    parser.add_argument("--type_filter", "-t", type=str, default=None, help="素材类型过滤")
    parser.add_argument("--mood_filter", "-m", type=str, default=None, help="情绪过滤")
    parser.add_argument("--min_score", "-s", type=float, default=0.0, help="最低相似度阈值")
    parser.add_argument("--health", action="store_true", help="检查服务健康状态")
    parser.add_argument("--embed", "-e", type=str, default=None, help="获取文本的 Embedding 向量")
    parser.add_argument("--host", type=str, default=None, help=f"服务地址 (默认 {SUCAI_HOST})")

    args = parser.parse_args()

    if args.host:
        SUCAI_HOST = args.host

    if args.health:
        result = health()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.embed:
        result = embed(args.embed)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.query:
        result = search(
            query=args.query,
            top_k=args.top_k,
            type_filter=args.type_filter,
            mood_filter=args.mood_filter,
            min_score=args.min_score,
        )
        print(_format_results(result))
    else:
        # 默认：检查健康状态
        print("未指定操作，检查服务健康状态...\n")
        result = health()
        if "error" in result:
            print(f"[服务不可达] {result['error']}")
            print(f"\n请先启动服务:\n  cd sucai && ..\\venv\\Scripts\\python.exe search_service.py")
        else:
            print(f"[服务正常] 模型: {result.get('model')} | 设备: {result.get('device')} | 集合: {result.get('collection')}")


if __name__ == "__main__":
    main()
