import json

from linebot.v3.messaging import FlexMessage
from mistletoe.block_token import Document

from md2lineflex.flex_message_renderer import FlexMessageRenderer, LinkMode
from md2lineflex.llm_utils import clean_llm_output


def to_flex(md_text: str, link_mode: LinkMode = "button") -> FlexMessage:
    """
    統合型 Markdown -> LINE SDK FlexMessage 変換関数

    1. Markdown text から FlexMessage オブジェクトを生成
    2. LINE Bot SDK で送信
       (flex_msg は linebot.v3.messaging.FlexMessage と互換性があります)

    Example:
        ```python
        flex_msg = to_flex(md_text)
        messaging_api.push_message(
            PushMessageRequest(
                to="USER_ID",
                messages=[flex_msg]
            )
        )
        ```
    """
    alt_text = clean_llm_output(md_text)

    with FlexMessageRenderer(link_mode) as renderer:
        # Document 全体の Bubble 構造（JSON文字列）を取得
        json_str = renderer.render(Document(md_text.splitlines(keepends=True)))
        bubble_dict = json.loads(json_str)

        # FlexMessage 全体を dict 形式で組み立てて from_dict で変換する
        # altText フィールドは 最大 400 文字らしい
        flex_message_dict = {
            "type": "flex",
            "altText": alt_text.strip()[:400],
            "contents": bubble_dict,
        }

        # from_dict を使うことで Pylance の引数不足エラーを回避
        return FlexMessage.from_dict(flex_message_dict)
