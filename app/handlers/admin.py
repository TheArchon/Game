# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝
"""Owner/admin command router."""
from __future__ import annotations
from aiogram import Router
from aiogram.filters import Command

def build_router(app):
    router = Router(name="admin")
    router.message.register(app.command_maintenance, Command("maintenance"))
    router.message.register(app.command_adminstats, Command("adminstats"))
    router.message.register(app.command_addcoupon, Command("addcoupon"))
    router.message.register(app.command_setbalance, Command("setbalance"))
    async def ban(message, command):
        await app.command_ban(message, command, True)
    async def unban(message, command):
        await app.command_ban(message, command, False)
    router.message.register(ban, Command("ban"))
    router.message.register(unban, Command("unban"))
    router.message.register(app.command_broadcast, Command("broadcast"))
    router.message.register(app.command_update, Command("update"))
    return router

