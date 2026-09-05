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

def language_keyboard(current: str = "en"):
    data=load(current); b=data["buttons"]; rows=[]; row=[]
    for code,name in data["languages"].items():
        row.append(btn(("✓ " if code==current else "")+name,f"lang:{code}","language"))
        if len(row)==2: rows.append(row); row=[]
    if row: rows.append(row)
    rows.append([btn(b["home"],"home","home")]); return kb(rows)
