from textwrap import dedent

import pytest
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.json import JSONSnapshotExtension

from md2lineflex.md_to_flex import to_flex

# note: uv run pytest -v --snapshot-update to update json files


@pytest.fixture
def json_snapshot(snapshot: SnapshotAssertion):
    # 毎回長々と書くのを防ぐため、カスタム拡張を適応したfixtureを作ります
    return snapshot.use_extension(JSONSnapshotExtension)


def test_snapshot_basic(json_snapshot: SnapshotAssertion):
    # テキストと箇条書きだけの最もシンプルな Markdown
    md_basic = dedent("""
        # テスト通知

        これは Markdown の変換テストです。

        - 項目 1
        - 項目 2
        """)

    # シミュレーターに貼るのは "contents" (Bubble 単体) の部分です
    md_basic_dict = to_flex(md_basic).to_dict()["contents"]

    assert md_basic_dict == json_snapshot


def test_snapshot_rich(json_snapshot: SnapshotAssertion):
    # パターン1: 主要な構造の詰め合わせ (見出し、太字、斜体、コード、箇条書き、引用)
    md_rich = dedent("""
        # LINE Bot 通知

        Markdown から **Flex Message** への自動変換テストです。

        - 箇条書き項目 1
        - `コード強調` 付きの項目 2
        - *斜体テキスト* もサポート

        > これは引用ブロックです。
        > 2行目の文章です。

        1. foo
        1. bar
        1. baz
        """)

    md_rich_dict = to_flex(md_rich).to_dict()["contents"]

    assert md_rich_dict == json_snapshot


def test_snapshot_edge(json_snapshot: SnapshotAssertion):
    # パターン 2: エッジケース (空文字、スペース、記号)
    md_edge = dedent("""
        # 空と特殊文字

        & < > " ' のエスケープ検証

        >
        """)

    md_edge_dict = to_flex(md_edge).to_dict()["contents"]

    assert md_edge_dict == json_snapshot


def test_snapshot_link(json_snapshot: SnapshotAssertion):
    # パターン 3: リンクボタンモード (link_mode="button")
    md_link = dedent("""
        公式ドキュメントは [こちら](https://developers.line.biz/) からご確認ください
        """)

    button_dict = to_flex(md_link, link_mode="button").to_dict()["contents"]

    assert button_dict == json_snapshot


def test_snapshot_table(json_snapshot: SnapshotAssertion) -> None:
    """Markdown の表 (Table) レンダリング構造のスナップショットテスト"""
    md_table = dedent("""
        # 表の検証

        | ヘッダー1 | ヘッダー2 | ヘッダー3 |
        | :--- | :---: | ---: |
        | データ1 | `code` | **太字データ** |
        | 空セルあり | | データ3 |
        """)

    # Flex Message のデータ構造 (dict) を取得
    flex_dict = to_flex(md_table).to_dict()

    # スナップショットの検証
    assert flex_dict["contents"] == json_snapshot
