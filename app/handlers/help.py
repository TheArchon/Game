# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝
"""Help/commands router."""
from __future__ import annotations
from aiogram import Router
from aiogram.filters import Command

def build_router(app):
    router = Router(name="help")
    router.message.register(app.command_help, Command(commands=["help", "commands"]))
    return router
