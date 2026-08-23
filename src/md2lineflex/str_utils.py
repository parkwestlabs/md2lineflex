import json


def to_json_utf8(data: dict | list[dict]) -> str:
    """dict または list[dict] を UTF-8（日本語そのまま）の JSON 文字列に変換する"""
    return json.dumps(data, ensure_ascii=False)
