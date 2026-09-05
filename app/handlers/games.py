# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝
"""Game and auction command router."""
from __future__ import annotations
from aiogram import Router
from aiogram.filters import Command

def build_router(app):
    router = Router(name="games")
    router.message.register(app.command_flip, Command("flip"))
    router.message.register(app.command_trust, Command("trust"))
    router.message.register(app.command_bid, Command("bid"))
    return router
