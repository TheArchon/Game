# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatType, ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, BotCommand
from aiogram.exceptions import TelegramBadRequest

from app.config import Config
from app.db import Database, now_iso
from app.emoji import render_message_emojis, render_help_page_emojis, tg_emoji
from app.formatting import md_to_html
from app.keyboards.home import home_keyboard
from app.keyboards.help import help_keyboard
from app.keyboards.profile import profile_keyboard
from app.keyboards.wallet import wallet_keyboard, leaderboard_keyboard
from app.keyboards.language import language_keyboard
from app.keyboards.games import trust_keyboard
from app.keyboards.common import kb, btn
from app.locales.loader import SUPPORTED, load, t, localize_result
from app.services.core import Cooldowns, Economy, Rewards, Games
from app.services.auction import AuctionService
from app.services.ai import AIService
from app.updater import update_and_validate, restart_process, UpdateError

log = logging.getLogger("gamebot")
FLIRT = [
    "You have a dangerous talent for making ordinary chats interesting. 😉",
    "If charm were currency, you would already be rich. ✨",
    "I had a clever line ready… then you smiled. 😌",
]
SHAYARI = [
    "Kuch lafz dil se nikal jaate hain,\nKuch log dil mein utar jaate hain. ✨",
    "Raat khamosh thi, baat khaas thi,\nBas tumhari ek muskaan paas thi. 🌙",
]


def _args(command: CommandObject | None) -> list[str]:
    return (command.args or "").split() if command and command.args else []


def _user(message: Message, db: Database, economy: Economy, cfg: Config):
    u = message.from_user
    assert u is not None
    economy.ensure(u.id, u.username or "", u.first_name or "User")
    db.ensure_chat(message.chat.id, message.chat.title or (f"{u.first_name} chat" if message.chat.type == ChatType.PRIVATE else ""))
    return u.id, db.user(u.id)


def _render(text: str) -> str:
    return md_to_html(render_message_emojis(str(text)))


def _content_text(text: str) -> str:
    return _render(text)


class GameBotApp:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.db = Database(cfg.database_path)
        self.economy = Economy(self.db, cfg.start_balance)
        self.rewards = Rewards(self.db, cfg.daily_reward, cfg.referral_reward, cfg.referral_milestones)
        self.games = Games(self.db)
        self.auction = AuctionService(self.db, cfg.bid_duration_minutes, cfg.bid_min)
        self.ai = AIService(self.db, cfg.ai_api_url, cfg.ai_api_key, cfg.ai_model, cfg.ai_system_prompt)
        self.cooldowns = Cooldowns()
        self.bot: Bot | None = None
        self.bot_id = 0
        self.bot_username = cfg.bot_username

    def owner(self, uid: int) -> bool:
        return uid in self.cfg.owner_ids

    def language(self, uid: int) -> str:
        row = self.db.user(uid)
        return row["language"] if row else "en"

    async def send(self, chat_id: int, text: str, **kwargs):
        assert self.bot
        return await self.bot.send_message(chat_id, _content_text(text), **kwargs)

    async def edit(self, message: Message, text: str, markup: InlineKeyboardMarkup | None = None):
        text = _content_text(text)
        try:
            if message.photo or message.caption is not None:
                return await message.edit_caption(caption=text, reply_markup=markup)
            return await message.edit_text(text=text, reply_markup=markup)
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc).lower():
                raise
            return message

    async def home(self, message: Message, uid: int):
        lang=self.language(uid); data=load(lang)
        heart=tg_emoji(self.cfg.emoji_heart,"💝")
        text=data["messages"]["start_caption"].format(heart=heart)
        path=self.cfg.start_image_path
        if not os.path.isabs(path): path=str(Path(__file__).resolve().parents[1]/path)
        markup=home_keyboard(self.bot_username,self.cfg.support_url,self.cfg.updates_url,self.cfg.owner_url,lang)
        if Path(path).is_file():
            from aiogram.types import FSInputFile
            await message.answer_photo(FSInputFile(path),caption=_content_text(text),reply_markup=markup)
        else:
            await message.answer(_content_text(text),reply_markup=markup)

    async def guard(self, message: Message, allow_maintenance: bool = False):
        uid,row=_user(message,self.db,self.economy,self.cfg)
        self.db.log_event("message",uid,message.chat.id,{"command":bool(message.text and message.text.startswith("/"))})
        if row["is_banned"]:
            await self.send(message.chat.id,load(row["language"])["messages"]["banned"]); return None
        if self.db.get_setting("maintenance","off")=="on" and not self.owner(uid) and not allow_maintenance:
            await self.send(message.chat.id,load(row["language"])["messages"]["maintenance"]); return None
        return uid

    async def is_admin(self, chat_id: int, uid: int) -> bool:
        if self.owner(uid): return True
        try:
            member=await self.bot.get_chat_member(chat_id,uid)
            return member.status in {"creator","administrator"}
        except Exception:
            return False

    def help_page(self,page:int,language:str):
        page=max(1,min(5,int(page))); section=load(language)["help"][str(page)]
        text=f"[[help_title]]*Help Center  {page}/5*\n\n[[help_heading]]{section['title']}\n\n{section['body']}"
        return render_help_page_emojis(text,page),help_keyboard(page,language,5)

    def profile(self,uid:int):
        row=self.db.user(uid); lang=row["language"]; data=load(lang); name=row["first_name"] or row["username"] or "User"
        shield=data["messages"]["shield_active"] if row["shield_until"] else data["messages"]["shield_inactive"]
        return data["messages"]["profile_template"].format(name=name,balance=int(row["balance"]),streak=int(row["streak"]),shield=shield,language=lang.upper()),profile_keyboard(lang)

    def wallet(self,uid:int):
        lang=self.language(uid); data=load(lang)
        return data["messages"]["wallet_template"].format(balance=self.economy.balance(uid),stolen=self.db.stolen_total(uid)),wallet_keyboard(lang)

    def leaderboard(self,kind:str,chat_id:int,uid:int):
        lang=self.language(uid); data=load(lang); titles={"richest":data["buttons"]["richest"],"charm":data["buttons"]["charm"],"chat":data["buttons"]["chat_top"],"global":data["buttons"]["global_chat"]}
        with self.db.connection() as c:
            if kind=="charm": rows=c.execute("""SELECT u.id,u.first_name,u.username,COALESCE(SUM(CASE WHEN t.kind='charm' THEN t.amount ELSE 0 END),0) score FROM users u LEFT JOIN transactions t ON t.user_id=u.id WHERE u.is_banned=0 GROUP BY u.id ORDER BY score DESC,u.id ASC LIMIT 10""").fetchall()
            elif kind=="chat": rows=c.execute("""SELECT u.id,u.first_name,u.username,COUNT(e.id) score FROM users u LEFT JOIN events e ON e.actor_id=u.id AND e.chat_id=? AND e.event_type='message' WHERE u.is_banned=0 GROUP BY u.id ORDER BY score DESC,u.id ASC LIMIT 10""",(chat_id,)).fetchall()
            elif kind=="global": rows=c.execute("""SELECT u.id,u.first_name,u.username,COUNT(e.id) score FROM users u LEFT JOIN events e ON e.actor_id=u.id AND e.event_type='message' WHERE u.is_banned=0 GROUP BY u.id ORDER BY score DESC,u.id ASC LIMIT 10""").fetchall()
            else: rows=c.execute("SELECT id,username,first_name,balance score FROM users WHERE is_banned=0 ORDER BY balance DESC,id ASC LIMIT 10").fetchall()
        lines=[f"🏆 *{data['messages']['leaderboard_title']} — {titles.get(kind,titles['richest'])}*",""]
        if not rows: lines.append(data["messages"]["leaderboard_empty"])
        else:
            for i,r in enumerate(rows,1): lines.append(f"*{i}.* {r['first_name'] or ('@'+r['username'] if r['username'] else 'User')} — `{int(r['score']):,}`")
        return "\n".join(lines),leaderboard_keyboard(lang)

    async def _broadcast(self,chat_id:int,uid:int,args:list[str]):
        lang=self.language(uid)
        if not self.owner(uid) or not args: return await self.send(chat_id,t(lang,"messages.broadcast_usage"))
        text=" ".join(args); sent=0
        with self.db.connection() as c: ids=[int(r[0]) for r in c.execute("SELECT id FROM users WHERE is_banned=0").fetchall()]
        for target in ids:
            try: await self.send(target,text); sent+=1
            except Exception: pass
        await self.send(chat_id,t(lang,"messages.broadcast_done",sent=sent))

    async def command_start(self,message:Message,command:CommandObject|None):
        uid=await self.guard(message,True)
        if uid is None:return
        args=_args(command)
        if args and args[0].startswith("ref_"):
            try: self.rewards.refer(uid,int(args[0][4:]))
            except (ValueError,TypeError): pass
        await self.home(message,uid)

    async def command_help(self,message:Message):
        uid=await self.guard(message,True)
        if uid is None:return
        text,markup=self.help_page(1,self.language(uid))
        path=self.cfg.start_image_path
        if not os.path.isabs(path):
            path=str(Path(__file__).resolve().parents[1]/path)
        if Path(path).is_file():
            from aiogram.types import FSInputFile
            await message.answer_photo(FSInputFile(path),caption=_content_text(text),reply_markup=markup)
        else:
            await message.answer(_content_text(text),reply_markup=markup)

    async def command_profile(self,message:Message):
        uid=await self.guard(message)
        if uid is None:return
        text,markup=self.profile(uid); await message.answer(_content_text(text),reply_markup=markup)

    async def command_wallet(self,message:Message):
        uid=await self.guard(message); 
        if uid is None:return
        text,markup=self.wallet(uid); await message.answer(_content_text(text),reply_markup=markup)

    async def command_leaderboard(self,message:Message):
        uid=await self.guard(message); 
        if uid is None:return
        text,markup=self.leaderboard("richest",message.chat.id,uid); await message.answer(_content_text(text),reply_markup=markup)

    async def command_checkin(self,message:Message):
        uid=await self.guard(message); 
        if uid is None:return
        ok,streak,balance=self.rewards.checkin(uid); lang=self.language(uid)
        status=t(lang,"messages.checkin_claimed" if ok else "messages.checkin_already")
        await self.send(message.chat.id,t(lang,"messages.checkin",status=status,streak=streak,balance=balance))

    async def command_invite(self,message:Message):
        uid=await self.guard(message); 
        if uid is None:return
        lang=self.language(uid); count=self.db.referral_count(uid); claimed=self.db.referral_milestones_claimed(uid); username=self.bot_username or "YourBotUsername"; data=load(lang)
        lines=[f"🎟️ *{data['messages']['invite_title']}*","",f"`https://t.me/{username}?start=ref_{uid}`","",data['messages']['invite_reward'].format(reward=self.cfg.referral_reward)]
        if self.cfg.referral_milestones:
            lines += ["",data['messages']['invite_milestones']]
            for milestone,bonus in self.cfg.referral_milestones:
                if count>=milestone: lines.append(f"• {milestone} → *{bonus:,}* — {data['messages']['milestone_claimed'] if milestone in claimed else data['messages']['milestone_ready']}")
                else: lines.append(data['messages']['milestone_progress'].format(current=count,target=milestone,remaining=milestone-count,reward=bonus))
        await self.send(message.chat.id,"\n".join(lines))

    async def command_redeem(self,message:Message,command:CommandObject|None):
        uid=await self.guard(message); 
        if uid is None:return
        args=_args(command); lang=self.language(uid)
        if not args:return await self.send(message.chat.id,t(lang,"messages.usage_redeem"))
        _,text=self.rewards.coupon(uid,args[0]); await self.send(message.chat.id,localize_result(lang,text))

    async def command_language(self,message:Message,command:CommandObject|None=None):
        uid=await self.guard(message); 
        if uid is None:return
        args=_args(command); lang=self.language(uid)
        if not args:return await message.answer(_content_text(load(lang)["messages"]["language_title"]),reply_markup=language_keyboard(lang))
        new=args[0].lower()
        if new not in SUPPORTED:return await self.send(message.chat.id,t(lang,"messages.language_available"))
        with self.db.connection() as c:c.execute("UPDATE users SET language=?,updated_at=? WHERE id=?",(new,now_iso(),uid)); c.commit()
        await self.send(message.chat.id,load(new)["messages"]["language_updated"])

    async def command_send(self,message:Message,command:CommandObject|None):
        uid=await self.guard(message); 
        if uid is None:return
        args=_args(command); target=message.reply_to_message.from_user.id if message.reply_to_message and message.reply_to_message.from_user else None; parts=list(args); lang=self.language(uid)
        if not target:
            for i,p in enumerate(parts[:2]):
                if p.startswith("@") and len(p)>1:
                    row=self.db.user_by_username(p)
                    if row: target=int(row["id"])
                    else:
                        try:
                            info=await self.bot.get_chat(p); target=int(info.id) if info.type==ChatType.PRIVATE else None
                            if target:self.economy.ensure(target,info.username or "",info.first_name or "User")
                        except Exception: target=None
                    parts.pop(i);break
                if p.lstrip("@").isdigit():target=int(p.lstrip("@"));parts.pop(i);break
        if not target or len(parts)!=1 or not parts[0].isdigit():return await self.send(message.chat.id,t(lang,"messages.usage_send"))
        _,text=self.db.transfer(uid,target,int(parts[0])); await self.send(message.chat.id,localize_result(lang,text))

    async def command_steal(self,message:Message,command:CommandObject|None):
        uid=await self.guard(message); 
        if uid is None:return
        args=_args(command); target=message.reply_to_message.from_user.id if message.reply_to_message and message.reply_to_message.from_user else None; requested=None; lang=self.language(uid)
        if args:
            if args[0].isdigit(): requested=int(args[0])
            elif args[0].startswith("@"):
                row=self.db.user_by_username(args[0]); target=int(row["id"]) if row else None
                if not target:
                    try:
                        info=await self.bot.get_chat(args[0]); target=int(info.id) if info.type==ChatType.PRIVATE else None
                        if target:self.economy.ensure(target,info.username or "",info.first_name or "User")
                    except Exception: target=None
                if len(args)>1 and args[1].isdigit():requested=int(args[1])
        if not target and args and args[0].lstrip("@").isdigit():target=int(args[0].lstrip("@"))
        if not target:return await self.send(message.chat.id,t(lang,"messages.usage_steal"))
        ok,text=self.economy.steal(uid,target,self.cooldowns,self.cfg.steal_cooldown,requested); await self.send(message.chat.id,localize_result(lang,text))

    async def command_shield(self,message:Message):
        uid=await self.guard(message); 
        if uid is None:return
        lang=self.language(uid); now=datetime.now(timezone.utc)
        with self.db.connection() as c:
            c.execute("BEGIN IMMEDIATE"); row=c.execute("SELECT balance,shield_until FROM users WHERE id=?",(uid,)).fetchone()
            if not row or int(row["balance"])<self.cfg.shield_cost:
                c.rollback(); return await self.send(message.chat.id,t(lang,"messages.shield_cost",cost=self.cfg.shield_cost))
            current=None
            if row["shield_until"]:
                try:current=datetime.fromisoformat(row["shield_until"])
                except ValueError:pass
            base=max(now,current) if current else now; until=(base+timedelta(hours=self.cfg.shield_hours)).isoformat(); stamp=now_iso()
            updated=c.execute("UPDATE users SET balance=balance-?,shield_until=?,updated_at=? WHERE id=? AND balance>=?",(self.cfg.shield_cost,until,stamp,uid,self.cfg.shield_cost))
            if updated.rowcount!=1:
                c.rollback();return await self.send(message.chat.id,t(lang,"messages.shield_failed"))
            c.execute("INSERT INTO transactions(user_id,amount,kind,note,created_at) VALUES(?,?,?,?,?)",(uid,-self.cfg.shield_cost,"shield","purchase",stamp));c.commit()
        await self.send(message.chat.id,t(lang,"messages.shield_activated",until=until[:19].replace("T"," ")))

    async def command_flip(self,message:Message,command:CommandObject|None):
        uid=await self.guard(message); 
        if uid is None:return
        args=_args(command);lang=self.language(uid)
        if not args or not args[0].isdigit():return await self.send(message.chat.id,t(lang,"messages.usage_flip",min=self.cfg.flip_min,max=self.cfg.flip_max))
        amount=int(args[0])
        if not self.cfg.flip_min<=amount<=self.cfg.flip_max:return await self.send(message.chat.id,t(lang,"messages.flip_range"))
        _,text=self.games.flip(uid,amount);await self.send(message.chat.id,localize_result(lang,text))

    async def command_trust(self,message:Message,command:CommandObject|None):
        uid=await self.guard(message); 
        if uid is None:return
        lang=self.language(uid); target=message.reply_to_message.from_user.id if message.reply_to_message and message.reply_to_message.from_user else None
        if not target:return await self.send(message.chat.id,t(lang,"messages.trust_reply"))
        args=_args(command);amount=0
        if args:
            if not args[0].isdigit():return await self.send(message.chat.id,t(lang,"messages.trust_usage"))
            amount=int(args[0])
        try:gid=self.games.create_trust(message.chat.id,uid,target,amount)
        except Exception as exc:return await self.send(message.chat.id,localize_result(lang,str(exc)))
        await self.send(message.chat.id,t(lang,"messages.trust_start",id=gid),reply_markup=trust_keyboard(gid,lang))

    async def command_bid(self,message:Message,command:CommandObject|None):
        uid=await self.guard(message); 
        if uid is None:return
        args=_args(command);lang=self.language(uid)
        if not args:return await self.send(message.chat.id,t(lang,"messages.bid_usage"))
        try:
            if args[0].lower()=="close" and len(args)>1:
                a=self.auction.close(int(args[1]),uid);return await self.send(message.chat.id,t(lang,"messages.bid_closed",id=a["id"],amount=a["current_bid"]))
            if len(args)>=2 and args[0].isdigit() and args[1].isdigit():
                old,_=self.auction.bid(int(args[0]),uid,int(args[1]));return await self.send(message.chat.id,t(lang,"messages.bid_accepted",amount=int(args[1]),old=old))
            if not self.owner(uid):return await self.send(message.chat.id,t(lang,"messages.bid_owner"))
            if not args[0].isdigit():return await self.send(message.chat.id,t(lang,"messages.bid_usage"))
            amount=int(args[0]);item=" ".join(args[1:]).strip() or "Kai’s active auction item";aid,ends=self.auction.create(message.chat.id,uid,item,amount)
            await self.send(message.chat.id,t(lang,"messages.auction_opened",id=aid,item=item,amount=amount,ends=ends))
        except Exception as exc:await self.send(message.chat.id,str(exc))

    async def command_charm(self,message:Message,kind:str):
        uid=await self.guard(message); 
        if uid is None:return
        target=message.reply_to_message.from_user.id if message.reply_to_message and message.reply_to_message.from_user else None;lang=self.language(uid)
        if not target:return await self.send(message.chat.id,t(lang,"messages.reply_flirt" if kind=="flirt" else "messages.reply_shayari"))
        import random
        text=random.choice(FLIRT if kind=="flirt" else SHAYARI)
        with self.db.connection() as c:c.execute("INSERT INTO transactions(user_id,amount,kind,note,created_at) VALUES(?,?,?,?,?)",(uid,1,"charm","flirt_or_shayari",now_iso()));c.commit()
        await self.send(message.chat.id,text,reply_to_message_id=message.reply_to_message.message_id)

    async def command_memory(self,message:Message):
        uid=await self.guard(message); 
        if uid is None:return
        self.db.clear_memory(uid,message.chat.id);await self.send(message.chat.id,t(self.language(uid),"messages.memory_cleared"))

    async def command_stats(self,message:Message):
        uid=await self.guard(message); 
        if uid is None:return
        lang=self.language(uid)
        if not self.owner(uid):return await self.send(message.chat.id,t(lang,"messages.stats_owner"))
        s=self.db.stats();await self.send(message.chat.id,t(lang,"messages.stats",users=s["users"],groups=s["groups"],balance=s["balance"]))

    async def command_ai(self,message:Message,command:CommandObject|None):
        uid=await self.guard(message); 
        if uid is None:return
        lang=self.language(uid)
        if message.chat.type not in {ChatType.GROUP,ChatType.SUPERGROUP}:return await self.send(message.chat.id,t(lang,"messages.group_ai_only"))
        args=_args(command)
        if not args or args[0].lower() not in {"on","off"}:return await self.send(message.chat.id,t(lang,"messages.ai_usage"))
        if not await self.is_admin(message.chat.id,uid):return await self.send(message.chat.id,t(lang,"messages.group_admins"))
        state=args[0].lower();self.db.set_setting(f"chat_ai:{message.chat.id}",state);await self.send(message.chat.id,t(lang,"messages.group_ai_state",state=state.upper()))

    async def command_maintenance(self,message:Message,command:CommandObject|None):
        uid=await self.guard(message,True); 
        if uid is None:return
        lang=self.language(uid)
        if not self.owner(uid):return await self.send(message.chat.id,t(lang,"messages.owner_required"))
        args=_args(command)
        if not args or args[0] not in {"on","off"}:return await self.send(message.chat.id,t(lang,"messages.maintenance_usage"))
        self.db.set_setting("maintenance",args[0]);await self.send(message.chat.id,t(lang,"messages.maintenance_state",state=args[0].upper()))

    async def command_adminstats(self,message:Message):
        uid=await self.guard(message,True); 
        if uid is None:return
        lang=self.language(uid)
        if not self.owner(uid):return await self.send(message.chat.id,t(lang,"messages.owner_required"))
        s=self.db.stats();await self.send(message.chat.id,t(lang,"messages.admin_stats",users=s["users"],groups=s["groups"],balance=s["balance"]))

    async def command_addcoupon(self,message:Message,command:CommandObject|None):
        uid=await self.guard(message,True); 
        if uid is None:return
        args=_args(command);lang=self.language(uid)
        if not self.owner(uid) or len(args)!=3:return await self.send(message.chat.id,t(lang,"messages.addcoupon_usage"))
        try: code,reward,uses=args[0].upper(),int(args[1]),int(args[2]);
        except ValueError:return await self.send(message.chat.id,t(lang,"messages.addcoupon_usage"))
        with self.db.connection() as c:c.execute("INSERT INTO coupons(code,reward,max_uses,created_at) VALUES(?,?,?,?)",(code,reward,uses,now_iso()));c.commit()
        await self.send(message.chat.id,t(lang,"messages.coupon_created"))

    async def command_setbalance(self,message:Message,command:CommandObject|None):
        uid=await self.guard(message,True); 
        if uid is None:return
        args=_args(command);lang=self.language(uid)
        if not self.owner(uid) or len(args)!=2:return await self.send(message.chat.id,t(lang,"messages.balance_usage"))
        try:target,amount=int(args[0]),int(args[1])
        except ValueError:return await self.send(message.chat.id,t(lang,"messages.balance_usage"))
        u=self.db.user(target)
        if not u:return await self.send(message.chat.id,t(lang,"messages.user_not_found"))
        self.db.add_balance(target,amount-int(u["balance"]),"admin_setbalance","owner");await self.send(message.chat.id,t(lang,"messages.balance_updated"))

    async def command_ban(self,message:Message,command:CommandObject|None,ban:bool):
        uid=await self.guard(message,True); 
        if uid is None:return
        args=_args(command);lang=self.language(uid)
        if not self.owner(uid) or not args:return await self.send(message.chat.id,t(lang,"messages.ban_usage"))
        try:target=int(args[0])
        except ValueError:return await self.send(message.chat.id,t(lang,"messages.ban_usage"))
        with self.db.connection() as c:c.execute("UPDATE users SET is_banned=? WHERE id=?",(1 if ban else 0,target));c.commit()
        await self.send(message.chat.id,t(lang,"messages.user_banned" if ban else "messages.user_unbanned"))

    async def command_broadcast(self,message:Message,command:CommandObject|None):
        uid=await self.guard(message,True); 
        if uid is None:return
        await self._broadcast(message.chat.id,uid,_args(command))

    async def command_update(self,message:Message):
        uid=await self.guard(message,True); 
        if uid is None:return
        lang=self.language(uid)
        if not self.owner(uid):return await self.send(message.chat.id,t(lang,"messages.update_access"))
        await self.send(message.chat.id,t(lang,"messages.update_started"))
        try:result=await asyncio.to_thread(update_and_validate)
        except UpdateError as exc:return await self.send(message.chat.id,t(lang,"messages.update_failed",error=str(exc)[:1200]))
        except Exception as exc:return await self.send(message.chat.id,t(lang,"messages.update_failed_unexpected",error=str(exc)[:1200]))
        if not result.changed:return await self.send(message.chat.id,t(lang,"messages.update_current",branch=result.branch,commit=result.new_commit[:12]))
        await self.send(message.chat.id,t(lang,"messages.update_success",old=result.old_commit[:12],new=result.new_commit[:12],branch=result.branch))
        await asyncio.sleep(1); restart_process()

    async def on_new_members(self,message:Message):
        if not message.new_chat_members:return
        uid,row=_user(message,self.db,self.economy,self.cfg)
        if any(m.id==self.bot_id for m in message.new_chat_members): self.db.log_event("bot_added",uid,message.chat.id,{"members":len(message.new_chat_members)})

    async def on_text(self,message:Message):
        if not message.text or message.text.startswith("/"):return
        uid=await self.guard(message)
        if uid is None:return
        chat_type=message.chat.type
        if chat_type==ChatType.PRIVATE:
            text=await asyncio.to_thread(self.ai.reply,uid,message.chat.id,message.text)
            await self.send(message.chat.id,text)
            return
        if chat_type in {ChatType.GROUP,ChatType.SUPERGROUP} and self.db.get_setting(f"chat_ai:{message.chat.id}","on")=="on":
            reply=message.reply_to_message
            triggered=bool(reply and reply.from_user and reply.from_user.id==self.bot_id) or (self.bot_username and f"@{self.bot_username.lower()}" in message.text.lower())
            if triggered:
                text=await asyncio.to_thread(self.ai.reply,uid,message.chat.id,message.text)
                await self.send(message.chat.id,text,reply_to_message_id=message.message_id)

    async def callback(self,query:CallbackQuery):
        if not query.from_user or not query.message:return
        uid=query.from_user.id;self.economy.ensure(uid,query.from_user.username or "",query.from_user.first_name or "User");lang=self.language(uid);data=query.data or "";message=query.message
        try:
            if self.db.user(uid)["is_banned"]:await query.answer(load(lang)["messages"]["banned"],show_alert=True);return
            if data.startswith("help:"):
                page=int(data.split(":",1)[1]);text,markup=self.help_page(page,lang);await self.edit(message,text,markup)
            elif data=="home":
                await self.edit(message,load(lang)["messages"]["home_short"],home_keyboard(self.bot_username,self.cfg.support_url,self.cfg.updates_url,self.cfg.owner_url,lang))
            elif data=="profile":
                text,markup=self.profile(uid);await self.edit(message,text,markup)
            elif data=="wallet":
                text,markup=self.wallet(uid);await self.edit(message,text,markup)
            elif data=="leaderboard" or data.startswith("lb:"):
                kind=data.split(":",1)[1] if ":" in data else "richest";text,markup=self.leaderboard(kind,message.chat.id,uid);await self.edit(message,text,markup)
            elif data=="language":
                await self.edit(message,load(lang)["messages"]["language_title"],language_keyboard(lang))
            elif data.startswith("lang:"):
                new=data.split(":",1)[1]
                if new not in SUPPORTED:raise ValueError("Unsupported language")
                with self.db.connection() as c:c.execute("UPDATE users SET language=?,updated_at=? WHERE id=?",(new,now_iso(),uid));c.commit()
                await query.answer(load(new)["messages"]["language_updated"]);text,markup=self.profile(uid);await self.edit(message,text,markup)
            elif data.startswith("trust:"):
                _,gid,choice=data.split(":",2);ok,raw=self.games.choose_trust(int(gid),uid,choice);localized=localize_result(lang,raw);await query.answer(localized,show_alert=not ok)
                if ok and "waiting" not in raw.lower():markup=None
                else:markup=trust_keyboard(int(gid),lang)
                await self.edit(message,f"🤝 *Trust Game #{gid}*\n\n{localized}",markup)
            elif data=="add":await query.answer(load(lang)["messages"]["add_hint"])
            elif data in {"support","updates","owner"}:
                await self.edit(message,load(lang)["messages"][data],kb([[btn(load(lang)["buttons"]["home"],"home","home")]]))
            elif data=="noop":await query.answer(load(lang)["messages"]["help_callback"])
            else:await query.answer(load(lang)["messages"]["unavailable"])
        except Exception as exc:
            log.exception("Callback failed: %s",exc)
            try:await query.answer(load("en")["messages"]["unable"],show_alert=True)
            except Exception:pass

    async def cleanup(self):
        self.games.expire_trust_games();self.auction.close_expired()

    async def run(self):
        self.bot=Bot(self.cfg.bot_token,default=DefaultBotProperties(parse_mode=ParseMode.HTML,link_preview_is_disabled=True))
        me=await self.bot.get_me();self.bot_id=me.id;self.bot_username=self.cfg.bot_username or (me.username or "")
        commands=[("start","Open Kai"),("help","Help & commands"),("profile","View your profile"),("wallet","View your wallet"),("leaderboard","Open leaderboards"),("checkin","Daily check-in"),("invite","Referral link"),("flirt","Send a playful line"),("shayari","Get a shayari"),("steal","Steal virtual coins"),("send","Send virtual coins"),("shield","Activate protection"),("flip","Flip for coins"),("trust","Start Trust game"),("bid","Open/place an auction bid"),("language","Change language")]
        await self.bot.set_my_commands([BotCommand(command=c,description=d) for c,d in commands])
        log.info("Starting @%s (%s)",me.username,me.id)
        asyncio.create_task(self._maintenance_loop())
        self.bot._gamebot_app = self
        from app.handlers.router import build_router
        dp=Dispatcher();dp.include_router(build_router(self))
        await dp.start_polling(self.bot,allowed_updates=dp.resolve_used_update_types())

    async def _maintenance_loop(self):
        while True:
            try:await self.cleanup()
            except Exception:log.exception("Cleanup failed")
            await asyncio.sleep(30)

APP:GameBotApp|None=None

def bind_handlers(app:GameBotApp):
    """Compatibility entry point returning the fully modular root router.

    New code should use :func:`app.handlers.router.build_router`; this helper
    remains for integrations that imported ``bind_handlers`` from older builds.
    """
    from app.handlers.router import build_router
    return build_router(app)


def main():
    global APP
    logging.basicConfig(level=logging.INFO,format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    cfg=Config.from_env();APP=GameBotApp(cfg);asyncio.run(APP.run())
