# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝

from __future__ import annotations
from .common import kb, btn
from app.locales.loader import load

def wallet_keyboard(language: str = "en"):
    b=load(language)["buttons"]
    return kb([[btn(b["profile"],"profile","profile"),btn(b["leaderboard"],"leaderboard","leaderboard")],[btn(b["home"],"home","home")]])

def leaderboard_keyboard(language: str = "en"):
    b=load(language)["buttons"]
    return kb([[btn(b["richest"],"lb:richest","richest"),btn(b["charm"],"lb:charm","charm")],[btn(b["chat_top"],"lb:chat","chat_top"),btn(b["global_chat"],"lb:global","global_chat")],[btn(b["home"],"home","home")]])
