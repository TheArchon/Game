# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝

from __future__ import annotations
from .common import kb, btn, url_btn
from app.locales.loader import load

def home_keyboard(bot_username: str = "", support_url: str = "", updates_url: str = "", owner_url: str = "", language: str = "en"):
    b = load(language)["buttons"]
    add_url = f"https://t.me/{bot_username.lstrip('@')}?startgroup=true" if bot_username else ""
    add = url_btn(b["add_group"], add_url, "add_group") if add_url else btn(b["add_group"], "add", "add_group")
    support = url_btn(b["support"], support_url, "support") if support_url else btn(b["support"], "support", "support")
    updates = url_btn(b["updates"], updates_url, "updates") if updates_url else btn(b["updates"], "updates", "updates")
    owner = url_btn(b["owner"], owner_url, "owner") if owner_url else btn(b["owner"], "owner", "owner")
    return kb([[add, btn(b["help"], "help:1", "help")], [support, updates], [owner, btn(b["language"], "language", "language")]])
