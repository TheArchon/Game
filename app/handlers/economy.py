# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝
"""Economy command router."""
from __future__ import annotations
from aiogram import Router
from aiogram.filters import Command

def build_router(app):
    router = Router(name="economy")
    router.message.register(app.command_send, Command("send"))
    router.message.register(app.command_steal, Command("steal"))
    router.message.register(app.command_shield, Command("shield"))
    return router
