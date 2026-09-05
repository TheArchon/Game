# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝

from __future__ import annotations

import re
from collections.abc import Iterable
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.emoji import custom_emoji_ids

_PREFIX = re.compile(r"^[\s\u2600-\u27BF\U0001F000-\U0001FAFF\u200d\ufe0f\u2640-\u2642\u2190-\u21ff\u2300-\u23ff\u25a0-\u25ff♙♨⌂]+")


def _button(text: str, emoji_key: str | None = None, **kwargs) -> InlineKeyboardButton:
    if emoji_key:
        emoji_id = custom_emoji_ids().get(emoji_key, "").strip()
        if emoji_id:
            text = _PREFIX.sub("", text).strip() or text
            kwargs["icon_custom_emoji_id"] = emoji_id
    return InlineKeyboardButton(text=text, **kwargs)


def btn(text: str, data: str, emoji_key: str | None = None) -> InlineKeyboardButton:
    return _button(text, emoji_key, callback_data=data)


def url_btn(text: str, url: str, emoji_key: str | None = None) -> InlineKeyboardButton:
    return _button(text, emoji_key, url=url)


def kb(rows: Iterable[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=list(rows))
