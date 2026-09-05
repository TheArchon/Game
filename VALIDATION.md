# Validation

This build was audited against the supplied GameBot source and migrated to Aiogram 3.x while preserving the original non-secret file surface and feature modules.

- `python3 -m pytest -q` -> **22 passed**
- `python3 scripts/smoke_test.py` -> **PASS**
- `python3 -m compileall -q .` -> **PASS**
- Original non-secret project files -> **all present**
- Locale parity: `en`, `hi`, `id`, `it`, `ur` -> **PASS**
- All original command names registered in Aiogram dispatcher -> **PASS**
- Premium custom emoji text path (`<tg-emoji>`) -> **PASS (static/code audit)**
- Premium custom emoji inline-button path (`icon_custom_emoji_id`) -> **PASS (static/code audit)**
- Final GameBot header on Python sources -> **PASS**
- Original SQLite/core tests -> **PASS**

## Environment limitation

The audit environment does not have network/DNS access, so `aiogram` could not be downloaded and installed here. Therefore a live import against the real installed Aiogram package and a real Telegram Bot API session could not be executed in this environment. The project declares `aiogram>=3.25,<4`, and the custom-emoji button field used by this project is supported by Aiogram 3.25+ / Telegram Bot API 9.4+.

A real Telegram token must never be placed in this archive. Configure `.env` on the VPS before starting the bot.
