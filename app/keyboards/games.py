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

def trust_keyboard(game_id: int, language: str = "en"):
    b=load(language)["buttons"]
    return kb([[btn(b["trust"],f"trust:{game_id}:trust","trust"),btn(b["betray"],f"trust:{game_id}:betray","betray")]])
