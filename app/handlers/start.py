# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝
"""Start command router."""
from __future__ import annotations
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.filters import Command

def build_router(app):
    router = Router(name="start")
    router.message.register(app.command_start, CommandStart())
    return router
