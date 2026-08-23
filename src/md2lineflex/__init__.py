from importlib.metadata import PackageNotFoundError, version

from md2lineflex.md_to_flex import to_flex

try:
    __version__ = version("md2lineflex")
except PackageNotFoundError:
    # 開発中（未インストール状態）のフォールバック
    __version__ = "0.0.0"

__all__ = ["__version__", "to_flex"]
