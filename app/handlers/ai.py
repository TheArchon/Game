# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝
"""AI command/message router."""
from __future__ import annotations
from aiogram import Router, F
from aiogram.filters import Command

def build_router(app):
    router = Router(name="ai")
    router.message.register(app.command_ai, Command("ai"))
    router.message.register(app.command_memory, Command(commands=["resmemory", "resetmemory"]))
    # General text is intentionally last; command routers get first chance to handle updates.
    router.message.register(app.on_text, F.text)
    return router
