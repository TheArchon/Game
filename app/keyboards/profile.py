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

def profile_keyboard(language: str = "en"):
    b=load(language)["buttons"]
    return kb([[btn(b["leaderboard"],"leaderboard","leaderboard"),btn(b["wallet"],"wallet","wallet")],[btn(b["language"],"language","language"),btn(b["home"],"home","home")]])
