import json
from urllib.parse import urlsplit

# リンクボタン (URIAction) に許可する URL スキーム
LINK_URL_SCHEMES = ("http", "https")

# 画像 (FlexImage) に許可する URL スキーム (LINE は画像に https を要求する)
IMAGE_URL_SCHEMES = ("https",)


def to_json_utf8(data: dict | list[dict]) -> str:
    """dict または list[dict] を UTF-8（日本語そのまま）の JSON 文字列に変換する"""
    return json.dumps(data, ensure_ascii=False)


def is_allowed_url(url: str, schemes: tuple[str, ...]) -> bool:
    """URL のスキームが許可リストに含まれ、ホストを持つ場合のみ True を返す

    javascript:, data:, file: などの危険なスキームや、
    空白・制御文字を含む URL は拒否する。
    """
    # 空白や制御文字を含む URL は、後段で別の値として解釈されうるため拒否する
    if any(ch.isspace() or ord(ch) < 0x20 for ch in url):  # noqa: PLR2004
        return False

    try:
        parts = urlsplit(url)
    except ValueError:
        return False

    return parts.scheme.lower() in schemes and bool(parts.netloc)
