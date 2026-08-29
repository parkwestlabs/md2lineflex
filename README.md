# md2lineflex - Markdown to LINE FlexMessage Converter

[![PyPI version](https://img.shields.io/pypi/v/md2lineflex.svg?color=blue)](https://pypi.org/project/md2lineflex/)
[![Python Versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://pypi.org/project/md2lineflex/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
<!-- [![Python Versions](https://img.shields.io/pypi/pyversions/md2lineflex.svg)](https://pypi.org/project/md2lineflex/) -->

A lightweight Python library that converts **Markdown text into LINE Bot Flex Messages** effortlessly.

Designed especially for LLM / Chatbot developers who want to render Markdown outputs (from OpenAI, Claude, etc.) as beautiful, structured LINE Flex Messages instead of plain text.

---

## Features

- 🚀 **Zero-Config Conversion:** Simply pass a Markdown string and get a LINE Messaging API compatible `FlexMessage` object or `dict`.
- 🎨 **Rich Component Support:** Supports Headings, Paragraphs, Lists, Code Blocks, Quotes, Links, Images, and Tables.
- 🔗 **Flexible Link Handling:** Render links as embedded URLs, inline text, or interactive LINE URI Action Buttons.
- 🛡️ **Type Safe:** Fully typed with `py.typed` marker (PEP 561) for modern IDE auto-completion.

---

## Installation

```bash
# Using uv (Recommended)
uv add md2lineflex

# Using pip
pip install md2lineflex
```

Prerequisite: Python `>= 3.10` and `line-bot-sdk >= 3.0.0`

---

## Quickstart

````python
from linebot.v3.messaging import PushMessageRequest
from md2lineflex import to_flex

md_text = """
## Hello LINE Bot!

This is **bold text** generated from Markdown.

- Feature 1: Automatic Flex Box layout
- Feature 2: Supports [Links](https://example.com)

```python
print("Hello World")
```
"""

# Convert Markdown to FlexMessage object
flex_message = to_flex(md_text, link_mode="button")

# Send via LINE Messaging API SDK
request = PushMessageRequest(to="USER_ID", messages=[flex_message])
messaging_api.push_message(request)
````

---

## Options

### Link Modes (`link_mode`)

You can control how Markdown links `[Title](https://...)` are rendered in the Flex Message:

| Mode | Description |
| :--- | :--- |
| `button` **(Default)** | Appends interactive URI action buttons below the text block. |
| `action` | Renders links in text format: `Title (https://...)`. |
| `url_text` | Renders links in text format: `Title [https://...]`. |

```python
flex_msg = to_flex(md_text, link_mode="button")
```

---

## Development & Contributing

See [DEVELOPMENT.md](DEVELOPMENT.md) for local setup, running tests, and contribution guidelines.

---

## License

This project is licensed under the MIT License.
