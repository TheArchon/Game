# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝
"""General/profile/language router."""
from __future__ import annotations
from aiogram import Router
from aiogram.filters import Command
from app.locales.loader import t

def build_router(app):
    router = Router(name="general")
    router.message.register(app.command_profile, Command("profile"))
    router.message.register(app.command_wallet, Command(commands=["wallet", "amount"]))
    router.message.register(app.command_leaderboard, Command("leaderboard"))
    router.message.register(app.command_checkin, Command("checkin"))
    router.message.register(app.command_invite, Command("invite"))
    router.message.register(app.command_redeem, Command("redeem"))
    router.message.register(app.command_language, Command("language"))
    router.message.register(app.command_stats, Command("stats"))
    async def flirt(message):
        await app.command_charm(message, "flirt")
    async def shayari(message):
        await app.command_charm(message, "shayari")
    async def ping(message):
        uid = await app.guard(message)
        if uid is not None:
            await app.send(message.chat.id, t(app.language(uid), "messages.ping"))
    router.message.register(flirt, Command("flirt"))
    router.message.register(shayari, Command("shayari"))
    router.message.register(ping, Command("ping"))
    return router
