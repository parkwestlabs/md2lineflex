import json
from textwrap import dedent

from linebot.v3.messaging import FlexBox, FlexBubble, FlexMessage, FlexText
from mistletoe.block_token import Document, Paragraph
from mistletoe.span_token import RawText
from mistletoe.token import Token

from md2lineflex.flex_message_renderer import FlexMessageRenderer
from md2lineflex.md_to_flex import to_flex


class TestMdToLineFlex:
    """to_flex 関数のテスト"""

    def test_basic_structure(self):
        """基本的な Markdown から FlexMessage オブジェクトが生成されること"""
        md_text = dedent("""\
            ## タイトル

            本文の**テキスト**です。
            """)

        flex_msg = to_flex(md_text)

        # 1. 戻り値の型と alt_text の検証
        assert isinstance(flex_msg, FlexMessage)
        assert flex_msg.type == "flex"
        assert flex_msg.alt_text == dedent("""\
            ## タイトル

            本文のテキストです。
            """).rstrip("\n")

        # 2. Bubble コンテナが含まれていること
        container = flex_msg.contents
        assert isinstance(container, FlexBubble)
        assert isinstance(container.body, FlexBox)

        # 3. 辞書表現 (to_dict) で要素構造を検証
        msg_dict = flex_msg.to_dict()
        body_contents = msg_dict["contents"]["body"]["contents"]

        # 見出しと本文の 2 つのコンポーネントが生成されていること
        assert len(body_contents) == 2

        # --- 1つ目: 見出し (Heading) ---
        assert body_contents[0]["type"] == "text"
        assert body_contents[0]["text"] == "タイトル"
        assert body_contents[0]["weight"] == "bold"

        # --- 2つ目: 本文 (Paragraph with Spans) ---
        p_block = body_contents[1]
        assert p_block["type"] == "text"
        assert "contents" in p_block

        # 子要素 (Span) の装飾構造をチェック
        spans = p_block["contents"]
        assert len(spans) == 3

        # "本文の" (通常テキスト)
        assert spans[0]["type"] == "span"
        assert spans[0]["text"] == "本文の"

        # "**テキスト**" (太字)
        assert spans[1]["type"] == "span"
        assert spans[1]["text"] == "テキスト"
        assert spans[1]["weight"] == "bold"

        # "です。" (通常テキスト)
        assert spans[2]["type"] == "span"
        assert spans[2]["text"] == "です。"

    def test_list_with_bold_formatting(self):
        """箇条書きリストが生成され項目内の太字(**)がspansのweight: boldに変換される"""
        md_text = dedent("""\
            - **項目1**
            - 項目2
            """)

        flex_msg = to_flex(md_text)
        msg_dict = flex_msg.to_dict()

        # リスト用 FlexBox の構造確認
        list_box = msg_dict["contents"]["body"]["contents"][0]
        assert list_box["type"] == "box"
        assert list_box["layout"] == "vertical"

        # リスト要素（ベースライン揃えの Box）の確認
        items = list_box["contents"]
        assert len(items) == 2

        # --- 項目1: **項目1** (太字) の検証 ---
        item1_box = items[0]

        # 一番外側のリスト項目コンテナは vertical
        assert item1_box["layout"] == "vertical"

        # 内側のマーカー＋本文の対和コンテナが baseline
        item1_baseline_box = item1_box["contents"][0]
        assert item1_baseline_box["layout"] == "baseline"

        # 太字の検証（baseline Box 内の本文テキストを参照）
        # contents[0] はマーカー("•")、contents[1] が本文 FlexText
        text_comp = item1_baseline_box["contents"][1]
        bold_span = text_comp["contents"][0]
        assert bold_span["text"] == "項目1"
        assert bold_span["weight"] == "bold"

        # 行頭記号 (•)
        assert item1_baseline_box["contents"][0]["text"] == "•"

        # 本文テキスト (FlexText の contents 内の spans を検証)
        item1_spans = item1_baseline_box["contents"][1]["contents"]
        assert len(item1_spans) == 1
        assert item1_spans[0]["type"] == "span"
        assert item1_spans[0]["text"] == "項目1"
        assert item1_spans[0]["weight"] == "bold"  # 太字が削除されず反映されていること

        # --- 項目2: 項目2 (通常テキスト) の検証 ---
        item2_baseline_box = items[1]["contents"][0]
        item2_spans = item2_baseline_box["contents"][1]["contents"]
        assert len(item2_spans) == 1
        assert item2_spans[0]["type"] == "span"
        assert item2_spans[0]["text"] == "項目2"
        assert "weight" not in item2_spans[0]  # 通常テキストには weight がないこと

    def test_code_fence(self):
        """コードブロックが指定した背景色のボックスとして生成されること"""
        md_text = dedent("""\
            ```python
            print("hello")
            ```
            """)

        flex_msg = to_flex(md_text)
        msg_dict = flex_msg.to_dict()

        code_box = msg_dict["contents"]["body"]["contents"][0]
        assert code_box["type"] == "box"
        assert code_box["backgroundColor"] == "#272822"  # ダーク背景

        code_text = code_box["contents"][0]["text"]
        assert code_text == 'print("hello")'

    def test_quote(self):
        """引用 (>) が装飾付きボックスとして生成され、内部テキストがspansで保持される"""
        md_text = "> これは引用文です。"

        flex_msg = to_flex(md_text)
        msg_dict = flex_msg.to_dict()

        # 1. 引用ボックストップレベルの検証
        quote_box = msg_dict["contents"]["body"]["contents"][0]
        assert quote_box["type"] == "box"
        assert quote_box["borderColor"] == "#cccccc"

        # 2. 引用内部のテキストコンポーネント (FlexText) の検証
        text_component = quote_box["contents"][0]
        assert text_component["type"] == "text"
        assert text_component["style"] == "italic"  # 引用文用のイタリック装飾

        # 3. spans の構造検証
        spans = text_component["contents"]
        assert len(spans) == 1
        assert spans[0]["type"] == "span"
        assert spans[0]["text"] == "これは引用文です。"

    def test_empty_markdown(self):
        """空の Markdown が入力されてもエラーにならず空の Bubble が返ること"""
        flex_msg = to_flex("")
        assert isinstance(flex_msg, FlexMessage)

        msg_dict = flex_msg.to_dict()
        assert msg_dict["contents"]["body"]["contents"] == [
            {
                "type": "text",
                "text": " ",
                "size": "sm",
                "color": "#111111",
                "weight": "bold",
                "wrap": True,
                "margin": "lg",
            }
        ]

    def test_spans_and_button_link(self):
        """太字、インラインコード、およびボタン型リンクの動作確認"""
        md_text = dedent("""\
            **太字** と `code` と [公式](https://line.biz) のテストです。
            """)

        flex_msg = to_flex(md_text, link_mode="button")
        msg_dict: dict = flex_msg.to_dict()

        body_contents = msg_dict["contents"]["body"]["contents"]

        # 1. Text コンポーネント内の spans の確認
        spans = body_contents[0]["contents"]
        assert spans[0]["text"] == "太字"
        assert spans[0]["weight"] == "bold"

        assert spans[2]["text"] == " code "
        assert spans[2]["color"] == "#0052cc"

        assert spans[4]["text"] == "公式"
        assert spans[4]["color"] == "#06c755"

        # 2. 直下に挿入された URI アクションボタンの確認
        button = body_contents[1]
        assert button["type"] == "button"
        assert button["action"]["uri"] == "https://line.biz"

    def test_thematic_break(self):
        """水平線 (---) の確認"""
        md_text = "---\n"
        flex_msg = to_flex(md_text)
        msg_dict = flex_msg.to_dict()

        sep = msg_dict["contents"]["body"]["contents"][0]
        assert sep["type"] == "separator"

    # -------------------------------------------------------------------------
    # 不具合検出用の追加テストケース（この2点をテストファイルに追加）
    # -------------------------------------------------------------------------

    def test_ordered_list_numbering(self):
        """順序付きリストが 1. 2. と正しく 1 から始まる番号で生成されること"""
        md_text = dedent("""\
            1. 第一項目
            2. 第二項目
            """)

        flex_msg = to_flex(md_text)
        msg_dict = flex_msg.to_dict()

        list_box = msg_dict["contents"]["body"]["contents"][0]
        items = list_box["contents"]

        # 0. ではなく 1. から始まっていることの検証
        assert items[0]["contents"][0]["contents"][0]["text"] == "1."
        assert items[1]["contents"][0]["contents"][0]["text"] == "2."

    def test_multiline_code_fence(self):
        """複数行のコードブロックで改行が保持されること"""
        md_text = dedent("""\
            ```python
            def hello():
                print("world")
            ```
            """)

        flex_msg = to_flex(md_text)
        msg_dict = flex_msg.to_dict()

        code_box = msg_dict["contents"]["body"]["contents"][0]
        code_text = code_box["contents"][0]["text"]

        # 改行が含まれて正しくインデントされていること
        assert code_text == 'def hello():\n    print("world")'

    def test_indent_block_code(self):
        """4スペースインデントによるコードブロックで改行が保持されること"""
        md_text = dedent("""\
            本文のテキスト

                def hello():
                    print("world")
            """)

        flex_msg = to_flex(md_text)
        msg_dict = flex_msg.to_dict()

        # 2番目のコンポーネント（CodeBlock）を取得
        code_box = msg_dict["contents"]["body"]["contents"][1]
        code_text = code_box["contents"][0]["text"]

        # 改行が含まれていることの検証
        assert code_text == 'def hello():\n    print("world")'

    def test_quote_multiline(self):
        """引用 (>) 内の連続した行が \n で結合され、LINE 上で改行表示されること"""
        md_text = dedent("""\
            > これは引用ブロックです。
            > 2行目の文章です。
            """)

        flex_msg = to_flex(md_text)
        msg_dict = flex_msg.to_dict()

        # 1. 引用ボックストップレベルの検証
        quote_box = msg_dict["contents"]["body"]["contents"][0]
        assert quote_box["type"] == "box"
        assert quote_box["layout"] == "vertical"

        # 2. 内部の FlexText は 1 つであることを確認
        quote_contents = quote_box["contents"]
        assert len(quote_contents) == 1

        # 3. FlexText の基本スタイル検証
        text_component = quote_box["contents"][0]
        assert text_component["type"] == "text"
        assert text_component["style"] == "italic"
        assert text_component["color"] == "#555555"

        # 4. spans 内のテキストを連結した時に、改行 (\n) が入っているか検証
        spans = text_component["contents"]
        full_text = "".join(s["text"] for s in spans)

        assert full_text == "これは引用ブロックです。\n2行目の文章です。"


class TestRenderParagraph:
    """FlexMessageRenderer.render_paragraph の単体テスト"""

    def _parse_paragraph(self, md_text: str) -> Paragraph:
        """Markdown 文字列から Paragraph トークンを取得するヘルパー関数"""
        doc = Document(md_text.splitlines(keepends=True))

        # Iterable から list に変換してからインデックス参照・型チェックを行う
        children = list(doc.children or [])
        assert children, "Document に子要素が存在しません"

        paragraph = children[0]
        assert isinstance(paragraph, Paragraph)
        return paragraph

    def test_plain_and_bold_text(self):
        """通常テキストと太字が正しく spans に分解されること"""
        md_text = "本文の**テキスト**です。"
        paragraph = self._parse_paragraph(md_text)

        renderer = FlexMessageRenderer()
        result_json = renderer.render_paragraph(paragraph)
        result_list: list[dict] = json.loads(result_json)

        # 戻り値がリストであり、先頭に FlexText が含まれていることの検証
        assert isinstance(result_list, list)
        text_comp = result_list[0]

        # 全体構造の検証
        assert text_comp["type"] == "text"
        assert text_comp["size"] == "sm"
        assert text_comp["color"] == "#333333"
        assert text_comp["wrap"] is True

        # spans の構造検証
        spans = text_comp["contents"]
        assert len(spans) == 3

        # 1. 通常テキスト
        assert spans[0]["type"] == "span"
        assert spans[0]["text"] == "本文の"
        assert "weight" not in spans[0]

        # 2. 太字
        assert spans[1]["type"] == "span"
        assert spans[1]["text"] == "テキスト"
        assert spans[1]["weight"] == "bold"

        # 3. 通常テキスト
        assert spans[2]["type"] == "span"
        assert spans[2]["text"] == "です。"

    def test_inline_code_and_emphasis(self):
        """インラインコードと斜体が正しく spans にスタイル適用されること"""
        md_text = "`code` と *斜体* のテスト"
        paragraph = self._parse_paragraph(md_text)

        renderer = FlexMessageRenderer()
        result_json = renderer.render_paragraph(paragraph)
        result_list = json.loads(result_json)

        assert isinstance(result_list, list)
        text_comp = result_list[0]

        spans = text_comp["contents"]
        assert len(spans) == 4

        # 0: インラインコード (`code`)
        assert spans[0]["type"] == "span"
        assert spans[0]["text"] == " code "
        assert spans[0]["color"] == "#0052cc"
        assert spans[0]["weight"] == "bold"

        # 1: 通常テキスト (" と ")
        assert spans[1]["type"] == "span"
        assert spans[1]["text"] == " と "
        assert "color" not in spans[1]  # スタイルが指定されていないこと

        # 2: 斜体 (*斜体*)
        assert spans[2]["type"] == "span"
        assert spans[2]["text"] == "斜体"
        assert spans[2]["style"] == "italic"
        assert spans[2]["color"] == "#555555"

        # 3: 通常テキスト (" のテスト")
        assert spans[3]["type"] == "span"
        assert spans[3]["text"] == " のテスト"
        assert "style" not in spans[3]

    def test_link_button_mode(self):
        """link_mode="button" の時、JSON の配列 (text + button) が返されること"""
        md_text = "詳細は [公式](https://example.com) を確認。"
        paragraph = self._parse_paragraph(md_text)

        renderer = FlexMessageRenderer(link_mode="button")
        result_json = renderer.render_paragraph(paragraph)

        # extras (ボタン) が存在するため、戻り値はリスト形式の JSON になる
        result_list: list[dict] = json.loads(result_json)
        assert isinstance(result_list, list)
        assert len(result_list) == 2

        # 1つ目: テキストブロック
        text_block = result_list[0]
        assert text_block["type"] == "text"
        assert text_block["contents"][1]["text"] == "公式"
        assert text_block["contents"][1]["color"] == "#06c755"

        # 2つ目: 追加された URI アクションボタン
        button_block = result_list[1]
        assert button_block["type"] == "button"
        assert button_block["action"]["type"] == "uri"
        assert button_block["action"]["uri"] == "https://example.com"
        assert button_block["action"]["label"] == "開く: 公式"

    def test_single_image(self):
        """段落内に画像単体のみが含まれる場合、Image コンポーネントが生成されること"""
        md_text = "![代替テキスト](https://example.com/image.png)"
        paragraph = self._parse_paragraph(md_text)

        renderer = FlexMessageRenderer()
        result_json = renderer.render_paragraph(paragraph)
        result_dict = json.loads(result_json)

        assert result_dict["type"] == "image"
        assert result_dict["url"] == "https://example.com/image.png"
        assert result_dict["size"] == "full"
        assert result_dict["aspectMode"] == "fit"


class TestCoverageEdgeCases:
    """カバレッジ向上のためのエッジケース・分岐網羅テスト"""

    # -------------------------------------------------------------------------
    # 1. _parse_span_tokens: link_mode 分岐の網羅
    # -------------------------------------------------------------------------
    def test_link_mode_action(self):
        """link_mode='action' の場合、URLがテキスト内に括弧付きで展開されること"""
        md_text = "詳細は [公式](https://example.com) をご覧ください。"

        # link_mode="action" を指定してレンダー
        flex_msg = to_flex(md_text, link_mode="action")
        msg_dict = flex_msg.to_dict()

        # body 内の paragraph を取得
        p_block = msg_dict["contents"]["body"]["contents"][0]
        spans = p_block["contents"]

        # リンク部分 (spans[1]) が "公式 (https://example.com)" に展開されていること
        assert spans[1]["type"] == "span"
        assert spans[1]["text"] == "公式 (https://example.com)"
        assert spans[1]["color"] == "#06c755"
        assert spans[1]["weight"] == "bold"

    def test_link_mode_url_text(self):
        """link_mode='url_text' (デフォルト/その他) の場合、[URL] の形式で展開される"""
        md_text = "[公式](https://example.com)"

        flex_msg = to_flex(md_text, link_mode="url_text")
        msg_dict = flex_msg.to_dict()

        p_block = msg_dict["contents"]["body"]["contents"][0]
        spans = p_block["contents"]

        assert spans[0]["text"] == "公式 [https://example.com]"

    # -------------------------------------------------------------------------
    # 2. _render_children: dict 単体が返ってきた場合の分岐通過
    # -------------------------------------------------------------------------
    def test_render_children_with_dict_component(self):
        """_render_children が FlexComponent オブジェクトのリストを返すことを検証"""
        md_text = dedent("""\
            # 見出し1

            普通の段落テキスト
            """)

        renderer = FlexMessageRenderer()
        doc = Document(md_text.splitlines(keepends=True))

        # _render_children を直接実行して、dict 要素が正しく平坦に格納されるか検証
        contents = renderer._render_children(doc)  # noqa: SLF001

        assert len(contents) == 2

        # 1. 見出し (FlexText オブジェクト)
        assert isinstance(contents[0], FlexText)
        assert contents[0].type == "text"
        assert contents[0].text == "見出し1"

        # 2. 段落 (FlexText オブジェクト - Span を含む場合 contents に FlexSpan が入る)
        assert isinstance(contents[1], FlexText)
        assert contents[1].type == "text"
        assert contents[1].contents is not None  # Span のリストが入っているか確認

    # -------------------------------------------------------------------------
    # 3. 未対応要素・空要素のフォールバック (安全策) の網羅
    # -------------------------------------------------------------------------
    def test_empty_quote(self):
        """空の引用ブロック (> ) が入力されても安全策でガードされること"""
        md_text = "> "
        flex_msg = to_flex(md_text)
        msg_dict = flex_msg.to_dict()

        quote_box = msg_dict["contents"]["body"]["contents"][0]
        assert quote_box["type"] == "box"
        assert len(quote_box["contents"]) > 0

    def test_unknown_inline_token_fallback(self):
        """_parse_span_tokens 内の else (未対応インライン要素) のフォールバック動作"""
        # mistletoe で HTML タグ等を混ぜた際のエッジケース
        md_text = "テキスト <span>HTML</span> のテスト"
        renderer = FlexMessageRenderer()
        doc = Document(md_text.splitlines(keepends=True))

        children = list(doc.children or [])

        paragraph = children[0]
        assert isinstance(paragraph, Paragraph)

        spans, _ = renderer._parse_span_tokens(paragraph)  # noqa: SLF001
        # エラーにならず全テキストが span として抽出されていること
        full_text = "".join(s.text or "" for s in spans)
        assert "HTML" in full_text

    # -------------------------------------------------------------------------
    # 4. _parse_span_tokens の elif child.children: と else: の通過テスト
    # -------------------------------------------------------------------------
    def test_parse_span_tokens_nested_and_fallback_branches(self):
        """_parse_span_tokens の elif child.children: と else: を通過させる"""
        renderer = FlexMessageRenderer()

        # --- テスト1: elif child.children: を通過させる設定 ---
        # _convert_child_to_span が None を返し、かつ children を持つダミートークン作成
        class DummyContainerToken(Token):
            def __init__(self) -> None:
                self.children = [RawText("ネストテキスト")]

        container_parent = Paragraph([])
        container_parent.children = [DummyContainerToken()]

        spans, _ = renderer._parse_span_tokens(container_parent)  # noqa: SLF001
        # 再帰的に内部の RawText が解析されて span に変換されていること
        assert len(spans) == 1
        assert spans[0].text == "ネストテキスト"

        # --- テスト2: else: (未対応インライン要素のフォールバック) を通過させる設定 ---
        # _convert_child_to_span が None を返し、children も持たない (空) ダミートークン
        class DummyLeafToken(Token):
            def __init__(self) -> None:
                self.children = []

        leaf_parent = Paragraph([])
        leaf_parent.children = [DummyLeafToken()]

        spans_fallback, _ = renderer._parse_span_tokens(leaf_parent)  # noqa: SLF001
        # else に到達し _get_plain_text 経由で空テキスト扱い（又は安全策処理）されること
        assert (
            len(spans_fallback) == 0
        )  # fallback_text が空文字のため spans に追加されない、または安全に処理終了
