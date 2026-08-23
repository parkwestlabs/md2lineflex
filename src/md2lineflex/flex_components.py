from linebot.v3.messaging import (
    FlexBox,
    FlexButton,
    FlexComponent,
    FlexImage,
    FlexSeparator,
    FlexSpan,
    FlexText,
    URIAction,
)

from md2lineflex.theme import EMPTY_CHAR, Color, Margin, Size

# 共通フォールバックオブジェクト
EMPTY_SPAN = FlexSpan(text=EMPTY_CHAR)
# contents に渡す用のリスト（読み取り専用想定）
EMPTY_SPANS = [EMPTY_SPAN]


def heading_component(text: str, level: int) -> FlexText:
    # text が空文字や None だった場合に半角スペース1文字にフォールバック
    safe_text = text if text and text.strip() else EMPTY_CHAR

    size_map = {1: Size.HEADING_H1, 2: Size.HEADING_H2}
    size = size_map.get(level, Size.BODY)

    return FlexText(
        text=safe_text,
        weight="bold",
        size=size,
        color=Color.HEADING,
        wrap=True,
        margin=Margin.HEADING,
    )  # pyright: ignore[reportCallIssue]


def paragraph_component(spans: list[FlexSpan]) -> FlexText:
    return FlexText(
        size=Size.BODY,
        wrap=True,
        margin=Margin.PARAGRAPH,
        color=Color.BODY,
        contents=spans or EMPTY_SPANS,
    )  # pyright: ignore[reportCallIssue]


def code_block_component(raw_code: str) -> FlexBox:
    return FlexBox(
        layout="vertical",
        backgroundColor=Color.BG_CODE_BLOCK,
        cornerRadius="sm",
        paddingAll="md",
        margin=Margin.BLOCK,
        contents=[
            FlexText(
                text=raw_code or EMPTY_CHAR,
                size=Size.CODE,
                color=Color.CODE_BLOCK_TEXT,  # abb2bf
                wrap=True,
            )  # pyright: ignore[reportCallIssue]
        ],
    )


def list_item_component(
    prefix: str,
    spans: list[FlexSpan],
    extras: list[FlexButton] | None = None,
) -> FlexBox:
    # 行頭記号用テキスト
    prefix_component = FlexText(
        text=prefix or EMPTY_CHAR,
        size=Size.BODY,
        color=Color.MUTED,
        flex=0,  # 幅固定
    )  # pyright: ignore[reportCallIssue]

    # 本文用テキスト (contents に spans を配置)
    text_component = FlexText(
        text=EMPTY_CHAR,  # デフォルト
        size=Size.BODY,
        color=Color.BODY,
        wrap=True,
        flex=1,  # 残りの幅を占有
        contents=spans or EMPTY_SPANS,
    )  # pyright: ignore[reportCallIssue]

    row_box = FlexBox(
        layout="baseline",
        spacing="sm",
        contents=[prefix_component, text_component],
    )  # pyright: ignore[reportCallIssue]

    item_contents: list[FlexComponent] = [row_box]

    # リンクボタン等の追加要素（extras）があれば下部に追加
    if extras:
        item_contents.extend(extras)

    return FlexBox(
        layout="vertical",
        spacing="xs",
        margin=Margin.LIST_ITEM,
        contents=item_contents,
    )  # pyright: ignore[reportCallIssue]


def quote_box_component(contents: list[FlexComponent]) -> FlexBox:
    # 引用テキストにスタイル (斜体・グレー色) を適用
    for item in contents:
        if isinstance(item, FlexText):
            item.style = "italic"
            item.color = Color.QUOTE

    # contents が万が一空の場合は空のテキストコンポーネントを補填 (None 回避)
    if not contents:
        empty_text = FlexText(
            size=Size.BODY,
            style="italic",
            color=Color.QUOTE,
            wrap=True,
            contents=EMPTY_SPANS,
        )  # pyright: ignore[reportCallIssue]
        contents = [empty_text]

    # 引用デザインを適用した FlexBox
    return FlexBox(
        type="box",
        layout="vertical",
        spacing="xs",
        backgroundColor=Color.BG_QUOTE,
        borderColor=Color.BORDER,
        borderWidth="semi-bold",
        paddingAll="md",
        margin=Margin.BLOCK,
        contents=contents,  # 絶対に None にならない list
    )  # pyright: ignore[reportCallIssue]


def link_button_component(link_text: str, target_url: str) -> FlexButton:
    return FlexButton(
        style="secondary",
        height="sm",
        margin="sm",
        action=URIAction(
            type="uri",
            label=f"開く: {link_text[:12]}",
            uri=target_url,
        ),  # pyright: ignore[reportCallIssue]
    )  # pyright: ignore[reportCallIssue]


def image_component(url: str) -> FlexImage:
    return FlexImage(
        url=url,
        size="full",
        aspectMode="fit",
        margin=Margin.BLOCK,
    )  # pyright: ignore[reportCallIssue]


def separator_component() -> FlexSeparator:
    return FlexSeparator(margin=Margin.HEADING, color=Color.SEPARATOR)


def table_cell_component(
    spans: list[FlexSpan], flex: int = 1, *, is_header: bool = False
) -> FlexBox:
    """表の 1 セルを生成 (ヘッダーの場合は太字・背景色を設定)"""
    # ヘッダーの場合は文字を太字に補正（個別指定がなければ）
    if is_header:
        for span in spans:
            if not span.weight:
                span.weight = "bold"

    text_comp = FlexText(
        type="text",
        contents=spans or EMPTY_SPANS,
        size=Size.TABLE_CELL,
        color=Color.HEADING if is_header else Color.BODY,
        wrap=True,
        flex=flex,
    )  # pyright: ignore[reportCallIssue]

    return FlexBox(
        layout="vertical",
        contents=[text_comp],
        flex=flex,
        paddingAll="xs",
        backgroundColor=Color.BG_TABLE_HEADER if is_header else Color.BG_TABLE_BODY,
    )  # pyright: ignore[reportCallIssue]


def table_row_component(cells: list[FlexBox], *, is_header: bool = False) -> FlexBox:
    """表の 1 行を横並び (horizontal) で生成"""
    return FlexBox(
        layout="horizontal",
        contents=cells,
        spacing="xs",
        borderWidth="1px" if is_header else "none",
        borderColor=Color.BORDER,
    )  # pyright: ignore[reportCallIssue]


def table_component(rows: list[FlexBox]) -> FlexBox:
    """表全体のコンテナを生成"""
    return FlexBox(
        layout="vertical",
        contents=rows,
        spacing="2px",  # 行間の微小スキマ（区切り線っぽく見せる効果）
        margin=Margin.BLOCK,
        backgroundColor=Color.BG_TABLE_BORDER,  # 背景色をグレーにして枠線効果を出す
        paddingAll="1px",
    )  # pyright: ignore[reportCallIssue]
