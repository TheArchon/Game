# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝
"""Top-level Aiogram router assembly."""
from __future__ import annotations
from aiogram import Router as AiogramRouter, F
from . import start, help as help_handlers, general, economy, games, ai, admin, callbacks

def build_router(app) -> AiogramRouter:
    root = AiogramRouter()
    # Order is deliberate: command routers first, generic text last.
    for module in (start, help_handlers, general, economy, games, admin, ai, callbacks):
        child = module.build_router(app)
        root.include_router(child)
    root.message.register(app.on_new_members, F.new_chat_members)
    return root

class Router:
    """Compatibility facade retained for extensions importing the old Router symbol."""
    def __init__(self, app):
        self.app = app
        self.router = build_router(app)
