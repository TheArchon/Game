# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝
"""Shared helpers used by the Aiogram handler modules."""
from __future__ import annotations
import random
from aiogram.types import Message

def user_from_message(message: Message) -> tuple[int, str, str]:
    user = message.from_user
    if user is None:
        raise ValueError("Message has no sender")
    return user.id, user.username or "", user.first_name or "User"

def target_id(message: Message) -> int | None:
    reply = message.reply_to_message
    return reply.from_user.id if reply and reply.from_user else None

def random_choice(values):
    return random.choice(values)
