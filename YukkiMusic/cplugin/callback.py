#
# Copyright (C) 2024-present by TeamYukki@Github, < https://github.com/TeamYukki >.
#
# This file is part of < https://github.com/TeamYukki/YukkiMusicBot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TeamYukki/YukkiMusicBot/blob/master/LICENSE >
#
# All rights reserved.
#
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from pytgcalls.types import MediaStream, AudioQuality
from random import choice

from config import *
import logging
from YukkiMusic.utils.thumbnails import gen_thumb
from .utils import (
    HELP_TEXT,
    PM_START_TEXT,
    helpmenu,
)
from .utils.dossier import *
from .utils.active import (
    is_active_chat,
    is_streaming,
    iss_streaming,
    stream_on,
    stream_off,
)
from YukkiMusic.misc import SUDOERS
from .utils.active import _clear_
from .utils.inline import close_key
from .play import pytgcalls
from YukkiMusic.misc import clonedb


@Client.on_callback_query(filters.regex("forceclose"))
async def close_(client, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    query, user_id = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(
                "» ɪᴛ'ʟʟ ʙᴇ ʙᴇᴛᴛᴇʀ ɪғ ʏᴏᴜ sᴛᴀʏ ɪɴ ʏᴏᴜʀ ʟɪᴍɪᴛs ʙᴀʙʏ.", show_alert=True
            )
        except:
            return
    await CallbackQuery.message.delete()
    try:
        await CallbackQuery.answer()
    except:
        return


@Client.on_callback_query(filters.regex("close"))
async def forceclose_command(client, CallbackQuery):
    try:
        await CallbackQuery.message.delete()
    except:
        return
    try:
        await CallbackQuery.answer()
    except:
        pass


@Client.on_callback_query(filters.regex("clone_help"))
async def help_menu(client, query: CallbackQuery):
    try:
        await query.answer()
    except:
        pass

    try:
        await query.edit_message_text(
            text=f"๏ ʜᴇʏ {query.from_user.mention}, 🥀\n\nᴘʟᴇᴀsᴇ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ғᴏʀ ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴɴᴀ ɢᴇᴛ ʜᴇʟᴘ.",
            reply_markup=helpmenu,
        )
    except Exception as e:
        logging.exception(e)
        return


@Client.on_callback_query(filters.regex("clone_cb"))
async def open_hmenu(client, query: CallbackQuery):
    callback_data = query.data.strip()
    cb = callback_data.split(None, 1)[1]
    vi = await client.get_me()
    h = vi.mention
    help_back = [
        [InlineKeyboardButton(text="✨ sᴜᴩᴩᴏʀᴛ ✨", url=SUPPORT_GROUP)],
        [
            InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="clone_help"),
            InlineKeyboardButton(text="ᴄʟᴏsᴇ", callback_data="close"),
        ],
    ]
    keyboard = InlineKeyboardMarkup(help_back)

    try:
        await query.answer()
    except:
        pass

    if cb == "play":
        await query.edit_message_text(HELP_TEXT.format(h), reply_markup=keyboard)
    if cb == "telegraph":
        await query.edit_message_text(TELEGRAPH, reply_markup=keyboard)
    if cb == "google":
        await query.edit_message_text(GOOGLE, reply_markup=keyboard)


@Client.on_callback_query(filters.regex("clone_home"))
async def home_fallen(client, query: CallbackQuery):
    try:
        await query.answer()
    except:
        pass
    try:
        vi = await client.get_me()
        pm_buttons = [
            [
                InlineKeyboardButton(
                    text="ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ",
                    url=f"https://t.me/{vi.username}?startgroup=true",
                )
            ],
            [InlineKeyboardButton(text="ʜᴇʟᴩ & ᴄᴏᴍᴍᴀɴᴅs", callback_data="clone_help")],
            [
                InlineKeyboardButton(text=" ᴄʜᴀɴɴᴇʟ ", url=SUPPORT_CHANNEL),
                InlineKeyboardButton(text=" sᴜᴩᴩᴏʀᴛ ", url=SUPPORT_GROUP),
            ],
            [
                InlineKeyboardButton(
                    text=" Dᴇᴠᴇʟᴏᴘᴇʀ ",
                    url=f"tg://openmessage?user_id={choice(OWNER_ID)}",
                ),
            ],
        ]

        await query.edit_message_text(
            text=PM_START_TEXT.format(
                query.from_user.first_name,
                vi.mention,
            ),
            reply_markup=InlineKeyboardMarkup(pm_buttons),
        )
    except Exception as e:
        logging.exception(e)
        return
