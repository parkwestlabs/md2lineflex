import json
from typing import Literal

from linebot.v3.messaging import (
    FlexBox,
    FlexBubble,
    FlexButton,
    FlexComponent,
    FlexSpan,
    FlexText,
)
from mistletoe.base_renderer import BaseRenderer
from mistletoe.block_token import (
    BlockCode,
    CodeFence,
    Document,
    Heading,
    List,
    ListItem,
    Paragraph,
    Quote,
    Table,
    TableCell,
    TableRow,
    ThematicBreak,
)
from mistletoe.span_token import (
    Emphasis,
    HtmlSpan,
    Image,
    InlineCode,
    LineBreak,
    Link,
    RawText,
    Strikethrough,
    Strong,
)
from mistletoe.token import Token

from md2lineflex.flex_components import (
    code_block_component,
    heading_component,
    image_component,
    link_button_component,
    list_item_component,
    paragraph_component,
    quote_box_component,
    separator_component,
    table_cell_component,
    table_component,
    table_row_component,
)
from md2lineflex.str_utils import to_json_utf8

LinkMode = Literal["url_text", "action", "button"]

# content 属性を持つ末端トークンの型定義 (型エイリアス)
LeafToken = RawText | LineBreak | HtmlSpan

# LINE Flex Message の構造
# - ブロック要素: FlexBox や FlexBubble（レイアウトの入れ物）
# - インライン要素: FlexText の中に入れる FlexSpan（文字装飾）

# mistletoe → LINE Flex Message
# Paragraph, Heading, List 等:
#   render_* で受けて FlexComponent を組み立てる
# Strong, Emphasis, Link 等:
#   _parse_span_tokens と _convert_child_to_span で一括して FlexSpan 群に変換する


class FlexMessageRenderer(BaseRenderer):
    """Markdown AST を LINE Flex Message (Bubble) 用の JSON 文字列に変換するRenderer"""

    def __init__(self, link_mode: LinkMode = "url_text") -> None:
        super().__init__()
        self.link_mode: LinkMode = link_mode

    # --- インライン要素 (spans & extra components) の抽出 ---

    def _parse_span_tokens(
        self, token: Token
    ) -> tuple[list[FlexSpan], list[FlexButton]]:
        """子要素から Flex Text 用の spans と、追加のコンポーネント (ボタン等) を抽出"""
        spans: list[FlexSpan] = []
        extras: list[FlexButton] = []

        for child in token.children or []:
            span = self._convert_child_to_span(child, self.link_mode)
            if span:
                spans.append(span)

                # リンクボタン (extra) の抽出 (Link かつ button モード時のみ)
                if isinstance(child, Link) and self.link_mode == "button":
                    link_text = self._get_plain_text(child)
                    link_button = link_button_component(link_text, child.target)
                    extras.append(link_button)

            # Paragraph やその他の容器トークンの場合は再帰的に子要素を解析
            elif child.children:
                sub_spans, sub_extras = self._parse_span_tokens(child)
                spans.extend(sub_spans)
                extras.extend(sub_extras)

            # その他の未対応インライン要素（安全策）
            else:
                fallback_text = self._get_plain_text(child)
                if fallback_text:
                    spans.append(FlexSpan(text=fallback_text))

        return spans, extras

    def _convert_child_to_span(  # noqa: PLR0911
        self, child: Token, link_mode: LinkMode
    ) -> FlexSpan | None:
        text = self._get_plain_text(child)

        match child:
            case RawText():
                # 空文字の場合は半角スペースにして LINE 仕様違反を防ぐ
                return FlexSpan(text=child.content or " ")
            case LineBreak():
                return FlexSpan(text="\n")
            case Strong():  # 太字
                return FlexSpan(text=text, weight="bold")
            case Emphasis():  # 斜体
                return FlexSpan(text=text, style="italic", color="#555555")
            case Strikethrough():
                return FlexSpan(text=text, decoration="line-through")
            case InlineCode():  # 行内コード
                return FlexSpan(text=f" {text} ", color="#0052cc", weight="bold")
            case Link():  # リンク ([text](url))
                if link_mode == "action":
                    return FlexSpan(text=f"{text} ({child.target})", color="#06c755", weight="bold")  # fmt: skip  # noqa: E501
                if link_mode == "button":
                    return FlexSpan(text=text, weight="bold", color="#06c755")
                return FlexSpan(text=f"{text} [{child.target}]")
            case _:
                return None

    def _get_plain_text(self, token: Token) -> str:
        """純粋な文字列だけを取り出すヘルパー"""

        # 1. content 属性を持つ末端ノードなら文字列を返す
        if isinstance(token, LeafToken):
            return token.content

        # 2. children を持つ容器ノードなら子要素をたどる (再帰処理)
        if token.children is not None:
            return "".join(self._get_plain_text(child) for child in token.children)

        # 3. Image などの特殊要素、又は children が None の場合はテキストなし (空文字)
        return ""

    # -------------------------------------------------------------------------
    # Helper Methods (共通処理)
    # -------------------------------------------------------------------------
    def _render_children(self, token: Token) -> list[FlexComponent]:
        """
        子トークン群をレンダリングし、FlexComponent オブジェクトのリストとして集約する
        """
        contents: list[FlexComponent] = []

        for child in token.children or []:
            rendered_str = self.render(child)
            if not rendered_str or not rendered_str.strip():
                continue

            parsed = json.loads(rendered_str.strip())

            # 単体要素をリストに統一してイテレート処理を共通化
            items = parsed if isinstance(parsed, list) else [parsed]

            contents.extend([FlexComponent.from_dict(item) for item in items])

        return contents

    # -------------------------------------------------------------------------
    # Block Renderers (ブロック要素のレンダリング)
    # -------------------------------------------------------------------------
    def render_document(self, token: Document) -> str:
        contents = self._render_children(token)

        # ドキュメントが空の場合の最小表示保証
        if not contents:
            # 空の Markdown の場合は安全なプレースホルダーテキストを設置
            contents = [heading_component(" ", 3)]

        # FlexBox と FlexBubble のインスタンスを from_dict で生成する
        body_box = FlexBox(
            layout="vertical",
            spacing="md",
            contents=contents,
        )  # pyright: ignore[reportCallIssue]

        bubble = FlexBubble(body=body_box)

        return to_json_utf8(bubble.to_dict())

    def render_heading(self, token: Heading) -> str:
        text = self._get_plain_text(token)
        heading = heading_component(text, token.level)
        return to_json_utf8(heading.to_dict())

    def render_paragraph(self, token: Paragraph) -> str:
        children = list(token.children or [])

        # 段落内に画像単体のみが含まれる場合の判定
        if len(children) == 1 and isinstance(children[0], Image):
            img_token = children[0]
            image = image_component(img_token.src)
            return to_json_utf8(image.to_dict())

        spans, extras = self._parse_span_tokens(token)

        # 段落テキスト（FlexText オブジェクト）を作成
        para = paragraph_component(spans)

        # 段落本体と追加のリンクボタン群をまとめる（すべて FlexComponent）
        components: list[FlexComponent] = [para, *extras]

        # リストを JSON 化して返却
        return to_json_utf8([c.to_dict() for c in components])

    def render_list(self, token: List) -> str:
        """リスト全体をレンダリング"""
        list_boxes: list[FlexComponent] = []

        # 連番管理用の状態フラグとカウンター
        is_ordered: bool | None = None
        current_num = 0

        # 最初の ListItem の leader (例: "1.", "-", "*") から番号付きリストか判定
        for child in token.children or []:
            if not isinstance(child, ListItem):
                continue

            if is_ordered is None:
                leader = child.leader
                clean_leader = leader.strip().rstrip(".")

                # プレフィックスの先頭が数字（例: "1"）なら番号付きリストと判定
                is_ordered = clean_leader.isdigit()
                if is_ordered:
                    current_num = int(clean_leader)

            # プレフィックスの生成
            if is_ordered:
                prefix = f"{current_num}."
                current_num += 1  # 2, 3... と自動インクリメント
            else:
                prefix = "•"

            # 子要素 (インライン装飾) の解析
            item_json = self.render_list_item(child, prefix)
            item_dict = json.loads(item_json)
            list_boxes.append(FlexComponent.from_dict(item_dict))

        list_container = FlexBox(
            layout="vertical",
            spacing="xs",
            margin="md",
            contents=list_boxes,
        )  # pyright: ignore[reportCallIssue]
        return to_json_utf8(list_container.to_dict())

    def render_list_item(self, token: ListItem, prefix: str = "•") -> str:
        """リスト項目 1 つを JSON 文字列としてレンダリング"""
        spans: list[FlexSpan] = []
        extras: list[FlexButton] = []

        # ListItem の子要素（Paragraph や RawText 等）から Span と Extras を抽出
        for child in token.children or []:
            child_spans, child_extras = self._parse_span_tokens(child)
            spans.extend(child_spans)
            extras.extend(child_extras)

        list_item = list_item_component(prefix, spans, extras)

        return to_json_utf8(list_item.to_dict())

    def render_block_code(self, token: CodeFence | BlockCode) -> str:
        """CodeFence と BlockCode の両方がここにルーティングされる"""
        raw_code = self._get_plain_text(token).strip()
        code_block = code_block_component(raw_code)
        return to_json_utf8(code_block.to_dict())

    def render_quote(self, token: Quote) -> str:
        """引用 (>) ブロックの描画"""
        contents = self._render_children(token)

        # 引用ブロック内の全テキスト要素の上マージンを無効化して余白重複を防ぐ
        for item in contents:
            if isinstance(item, FlexText):
                item.margin = "none"

        quote_box = quote_box_component(contents)
        return to_json_utf8(quote_box.to_dict())

    def render_thematic_break(self, token: ThematicBreak) -> str:  # noqa: ARG002
        """水平線 (---)"""
        separator = separator_component()
        return to_json_utf8(separator.to_dict())

    def render_table(self, token: Table) -> str:
        """Markdown Table を FlexBox のグリッドレイアウトとして描画"""
        row_boxes: list[FlexBox] = []

        # ヘッダー行 (token.header) の処理
        if token.header is not None:
            header_box = self._render_table_row(token.header, is_header=True)
            if header_box:
                row_boxes.append(header_box)

        # 本文データ行 (token.children) の処理
        for child in token.children or []:
            # Table の children には必ず TableRow が入っているはず
            if not isinstance(child, TableRow):
                continue

            row_box = self._render_table_row(child, is_header=False)
            if row_box:
                row_boxes.append(row_box)

        # 表全体 Component の作成
        table_container = table_component(row_boxes)
        return to_json_utf8(table_container.to_dict())

    def _render_table_row(self, row: TableRow, *, is_header: bool) -> FlexBox | None:
        cell_boxes: list[FlexBox] = []

        for cell in row.children or []:
            if isinstance(cell, TableCell):
                spans, _ = self._parse_span_tokens(cell)
                if not spans:
                    spans = [FlexSpan(text=" ")]  # 空セル対策
                cell_boxes.append(table_cell_component(spans, is_header=is_header))

        if not cell_boxes:
            return None

        return table_row_component(cell_boxes, is_header=is_header)
