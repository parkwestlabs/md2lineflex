# 1. 正常にインポートできるか（配布物に必要なファイルが漏れているとここで失敗する）
import md2lineflex

# 2. バージョン情報が取得できるか
print(f"Loaded md2lineflex version: {md2lineflex.__version__}")  # noqa: T201

# 3. コア機能がエラーなく1回動くか（簡単な呼び出し）
# 例: マークダウン文字列を入れたらFlex Messageの辞書データが返ってくるか
result = md2lineflex.to_flex("# Hello")
assert result is not None

print("Smoke test passed successfully!")  # noqa: T201
