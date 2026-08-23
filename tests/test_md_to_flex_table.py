import json
from textwrap import dedent

from mistletoe.block_token import Document, Table

from md2lineflex.flex_message_renderer import FlexMessageRenderer
from md2lineflex.md_to_flex import to_flex


def test_table_rendering_structure():
    """Markdown の表(Table)の FlexBox グリッド構造(Table -> Row -> Cell)への変換"""
    md_text = dedent("""\
        | ヘッダー1 | ヘッダー2 |
        | --- | --- |
        | 値1 | 値2 |
        """)

    flex_msg = to_flex(md_text)
    msg_dict = flex_msg.to_dict()

    # body 直下のコンテナを取得
    body_contents = msg_dict["contents"]["body"]["contents"]
    table_box = body_contents[0]

    # 1. 表全体 (Table) の検証
    assert table_box["type"] == "box"
    assert table_box["layout"] == "vertical"
    assert len(table_box["contents"]) == 2  # ヘッダー行 + データ行 の計2行

    # 2. ヘッダー行 (Row 0) の検証
    header_row = table_box["contents"][0]
    assert header_row["type"] == "box"
    assert header_row["layout"] == "horizontal"
    assert len(header_row["contents"]) == 2

    # ヘッダーセル 0 (ヘッダー1) の検証
    header_cell_0 = header_row["contents"][0]
    assert header_cell_0["type"] == "box"
    assert header_cell_0["layout"] == "vertical"
    header_text_comp = header_cell_0["contents"][0]
    assert header_text_comp["type"] == "text"

    # ヘッダーの文字が bold (太字) に設定されていることの検証
    header_span_0 = header_text_comp["contents"][0]
    assert header_span_0["text"] == "ヘッダー1"
    assert header_span_0["weight"] == "bold"

    # 3. データ行 (Row 1) の検証
    data_row = table_box["contents"][1]
    assert data_row["type"] == "box"
    assert data_row["layout"] == "horizontal"

    # データセル 0 (値1) の検証
    data_cell_0 = data_row["contents"][0]
    data_text_comp = data_cell_0["contents"][0]
    data_span_0 = data_text_comp["contents"][0]
    assert data_span_0["text"] == "値1"
    # データ行のテキストにはデフォルトで weight="bold" が付与されていないこと
    assert "weight" not in data_span_0 or data_span_0["weight"] != "bold"


def test_table_with_formatting():
    """表セル内のインライン装飾(太字・コード等)が正しくスパンに反映されること"""
    md_text = dedent("""\
        | 機能 | 状態 |
        | --- | --- |
        | **太字テスト** | `code` |
        """)

    renderer = FlexMessageRenderer()
    doc = Document(md_text.splitlines(keepends=True))

    # doc.children から Table トークンを取得
    table_token = next(c for c in doc.children or [] if isinstance(c, Table))
    result_json = renderer.render_table(table_token)
    table_dict = json.loads(result_json)

    # データ行 (行 index: 1) のセル検証
    data_row = table_dict["contents"][1]

    # セル0: **太字テスト**
    cell_0_text = data_row["contents"][0]["contents"][0]
    span_0 = cell_0_text["contents"][0]
    assert span_0["text"] == "太字テスト"
    assert span_0["weight"] == "bold"

    # セル1: `code` (インラインコード)
    cell_1_text = data_row["contents"][1]["contents"][0]
    span_1 = cell_1_text["contents"][0]
    assert "code" in span_1["text"]
    assert span_1["color"] == "#0052cc"  # InlineCode の設定カラー
