#
# Copyright (C) 2024-present by TeamYukki@Github, < https://github.com/TeamYukki >.
#
# This file is part of < https://github.com/TeamYukki/YukkiMusicBot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TeamYukki/YukkiMusicBot/blob/master/LICENSE >
#
# All rights reserved.
#

import asyncio
import os
import logging
from ntgcalls import TelegramServerError, ConnectionError
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, MessageEntityType
from pyrogram.errors import (
    ChatAdminRequired,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from pytgcalls import PyTgCalls
from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Audio,
    Voice,
)
from pytgcalls.exceptions import (
    NoActiveGroupCall,
    UnMuteNeeded,
    NotInCallError,
    AlreadyJoinedError,
)
from pytgcalls.types import MediaStream, AudioQuality
from youtube_search import YoutubeSearch
from datetime import datetime

import config
from config import DURATION_LIMIT_MIN
from YukkiMusic.misc import clonedb
from YukkiMusic.cplugin.utils import add_active_chat, is_active_chat, stream_on
from YukkiMusic.utils.downloaders import audio_dl
from YukkiMusic.utils.thumbnails import gen_qthumb
from YukkiMusic.utils.thumbnails import gen_thumb

from typing import Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Audio, Message, Voice
from YukkiMusic.utils.database import get_assistant
from YukkiMusic import userbot
from YukkiMusic.core.call import Yukki
from .utils.inline import close_key
from .utils.active import _clear_


def get_url(message_1: Message) -> Union[str, None]:
    messages = [message_1]

    if message_1.reply_to_message:
        messages.append(message_1.reply_to_message)

    text = ""
    offset = None
    length = None

    for message in messages:
        if offset:
            break

        if message.entities:
            for entity in message.entities:
                if entity.type == MessageEntityType.URL:
                    text = message.text or message.caption
                    offset, length = entity.offset, entity.length
                    break

    if offset in (None,):
        return None

    return text[offset : offset + length]


def get_file_name(audio: Union[Audio, Voice]):
    return f'{audio.file_unique_id}.{audio.file_name.split(".")[-1] if not isinstance(audio, Voice) else "ogg"}'


pytgcalls = Yukki.one
app2 = userbot.one


class DurationLimitError(Exception):
    pass


@Client.on_message(
    filters.command(["play", "vplay", "p"])
    & filters.group
    & ~filters.forwarded
    & ~filters.via_bot
)
async def play(client, message: Message):
    msg = await message.reply_text("🔎")
    if len(message.command) < 2:
        return await msg.edit_text("» ᴡʜᴀᴛ ᴅᴏ ʏᴏᴜ ᴡᴀɴɴᴀ ᴘʟᴀʏ ʙᴀʙʏ ?")
    vi = await app2.get_me()
    viv = await client.get_me()
    BOT_USERNAME = viv.username
    try:
        await message.delete()
    except:
        pass

    try:
        try:
            get = await client.get_chat_member(message.chat.id, vi.username)
        except ChatAdminRequired:
            return await msg.edit_text(
                f"» ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴs ᴛᴏ ɪɴᴠɪᴛᴇ ᴜsᴇʀs ᴠɪᴀ ʟɪɴᴋ ғᴏʀ ɪɴᴠɪᴛɪɴɢ {viv.mention} ᴀssɪsᴛᴀɴᴛ ᴛᴏ {message.chat.title}."
            )
        if get.status == ChatMemberStatus.BANNED:
            return await msg.edit_text(
                text=f"» {viv.mention} ᴀssɪsᴛᴀɴᴛ ɪs ʙᴀɴɴᴇᴅ ɪɴ {message.chat.title}\n\n𖢵 ɪᴅ : `{vi.id}`\n𖢵 ɴᴀᴍᴇ : {vi.mention}\n𖢵 ᴜsᴇʀɴᴀᴍᴇ : @{vi.username}\n\nᴘʟᴇᴀsᴇ ᴜɴʙᴀɴ ᴛʜᴇ ᴀssɪsᴛᴀɴᴛ ᴀɴᴅ ᴘʟᴀʏ ᴀɢᴀɪɴ...",
            )
    except UserNotParticipant:
        if message.chat.username:
            invitelink = message.chat.username
            try:
                await app2.resolve_peer(invitelink)
            except Exception as ex:
                logging.exception(ex)
        else:
            try:
                invitelink = await client.export_chat_invite_link(message.chat.id)
            except ChatAdminRequired:
                return await msg.edit_text(
                    f"» ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴs ᴛᴏ ɪɴᴠɪᴛᴇ ᴜsᴇʀs ᴠɪᴀ ʟɪɴᴋ ғᴏʀ ɪɴᴠɪᴛɪɴɢ {viv.mention} ᴀssɪsᴛᴀɴᴛ ᴛᴏ {message.chat.title}."
                )
            except Exception as ex:
                return await msg.edit_text(
                    f"ғᴀɪʟᴇᴅ ᴛᴏ ɪɴᴠɪᴛᴇ {viv.mention} ᴀssɪsᴛᴀɴᴛ ᴛᴏ {message.chat.title}.\n\n**ʀᴇᴀsᴏɴ :** `{ex}`"
                )
        if invitelink.startswith("https://t.me/+"):
            invitelink = invitelink.replace("https://t.me/+", "https://t.me/joinchat/")
        anon = await msg.edit_text(
            f"ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...\n\nɪɴᴠɪᴛɪɴɢ {vi.mention} ᴛᴏ {message.chat.title}."
        )
        try:
            await app2.join_chat(invitelink)
            await asyncio.sleep(2)
            await msg.edit_text(
                f"{vi.mention} ᴊᴏɪɴᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ,\n\nsᴛᴀʀᴛɪɴɢ sᴛʀᴇᴀᴍ..."
            )
        except UserAlreadyParticipant:
            pass
        except Exception as ex:
            return await msg.edit_text(
                f"ғᴀɪʟᴇᴅ ᴛᴏ ɪɴᴠɪᴛᴇ {viv.mention} ᴀssɪsᴛᴀɴᴛ ᴛᴏ {message.chat.title}.\n\n**ʀᴇᴀsᴏɴ :** `{ex}`"
            )
        try:
            await app2.resolve_peer(invitelink)
        except:
            pass

    ruser = message.from_user.first_name
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    url = get_url(message)
    duration = None
    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT_MIN:
            raise DurationLimitError(
                f"» sᴏʀʀʏ ʙᴀʙʏ, ᴛʀᴀᴄᴋ ʟᴏɴɢᴇʀ ᴛʜᴀɴ  {DURATION_LIMIT_MIN} ᴍɪɴᴜᴛᴇs ᴀʀᴇ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ ᴛᴏ ᴘʟᴀʏ ᴏɴ {viv.mention}."
            )
        file_name = get_file_name(audio)
        title = file_name
        duration = round(audio.duration / 60)
        file_path = (
            await message.reply_to_message.download(file_name)
            if not os.path.isfile(os.path.join("downloads", file_name))
            else f"downloads/{file_name}"
        )
    elif url:
        try:
            results = YoutubeSearch(url, max_results=1).to_dict()
            title = results[0]["title"]
            duration = results[0]["duration"]
            videoid = results[0]["id"]

            secmul, dur, dur_arr = 1, 0, duration.split(":")
            for i in range(len(dur_arr) - 1, -1, -1):
                dur += int(dur_arr[i]) * secmul
                secmul *= 60

        except Exception as e:
            return await msg.edit_text(f"sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ\n\n**ᴇʀʀᴏʀ :** `{e}`")

        if (dur / 60) > DURATION_LIMIT_MIN:
            return await msg.edit_text(
                f"» sᴏʀʀʏ ʙᴀʙʏ, ᴛʀᴀᴄᴋ ʟᴏɴɢᴇʀ ᴛʜᴀɴ  {DURATION_LIMIT_MIN} ᴍɪɴᴜᴛᴇs ᴀʀᴇ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ ᴛᴏ ᴘʟᴀʏ ᴏɴ {viv.mention}."
            )
        file_path = audio_dl(url)
    else:
        if len(message.command) < 2:
            return await msg.edit_text("» ᴡʜᴀᴛ ᴅᴏ ʏᴏᴜ ᴡᴀɴɴᴀ ᴘʟᴀʏ ʙᴀʙʏ ?")
        await msg.edit_text("» ᴘʀᴏᴄᴇssɪɴɢ, ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...")
        query = message.text.split(None, 1)[1]
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            url = f"https://youtube.com{results[0]['url_suffix']}"
            title = results[0]["title"]
            videoid = results[0]["id"]
            duration = results[0]["duration"]

            secmul, dur, dur_arr = 1, 0, duration.split(":")
            for i in range(len(dur_arr) - 1, -1, -1):
                dur += int(dur_arr[i]) * secmul
                secmul *= 60

        except Exception as e:
            logging.exception(str(e))
            return await msg.edit(
                f"» ғᴀɪʟᴇᴅ ᴛᴏ ᴘʀᴏᴄᴇss ᴏ̨ᴜᴇʀʏ, ᴛʀʏ ᴘʟᴀʏɪɴɢ ᴀɢᴀɪɴ...\n{e}"
            )

        if (dur / 60) > DURATION_LIMIT_MIN:
            return await msg.edit(
                f"» sᴏʀʀʏ ʙᴀʙʏ, ᴛʀᴀᴄᴋ ʟᴏɴɢᴇʀ ᴛʜᴀɴ  {DURATION_LIMIT_MIN} ᴍɪɴᴜᴛᴇs ᴀʀᴇ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ ᴛᴏ ᴘʟᴀʏ ᴏɴ {viv.mention}."
            )
        file_path = audio_dl(url)

    try:
        videoid = videoid
    except:
        videoid = "fuckitstgaudio"
    if await is_active_chat(message.chat.id):
        stream = MediaStream(file_path, audio_parameters=AudioQuality.HIGH)
        try:
            await pytgcalls.play(
                message.chat.id,
                stream,
            )
            imgp = await gen_thumb(videoid)
            await message.reply_photo(
                photo=imgp,
                caption=f"**✮ 𝐒ʈᴧʀʈ𝛆ɗ 𝐒ʈʀ𝛆ɑɱɩŋʛ ✮**\n\n**✮ 𝐓ɩttɭ𝛆 ✮** [{title[:27]}](https://t.me/{viv.username}?start=info_{videoid})\n**✬ 𝐃ʋɽɑʈɩσŋ ✮** `{duration}` ᴍɪɴ\n**✭ 𝐁ɣ ✮** {ruser}",
                reply_markup=close_key,
            )
            await msg.delete()
        except NotInCallError:
            stream = MediaStream(file_path, audio_parameters=AudioQuality.HIGH)
            try:
                await pytgcalls.play(
                    message.chat.id,
                    stream,
                )

            except NoActiveGroupCall:
                return await msg.edit_text(
                    "**» ɴᴏ ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ ғᴏᴜɴᴅ.**\n\nᴩʟᴇᴀsᴇ ᴍᴀᴋᴇ sᴜʀᴇ ʏᴏᴜ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ."
                )
            except TelegramServerError:
                return await msg.edit_text(
                    "» ᴛᴇʟᴇɢʀᴀᴍ ɪs ʜᴀᴠɪɴɢ sᴏᴍᴇ ɪɴᴛᴇʀɴᴀʟ ᴘʀᴏʙʟᴇᴍs, ᴘʟᴇᴀsᴇ ʀᴇsᴛᴀʀᴛ ᴛʜᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ."
                )
            except UnMuteNeeded:
                return await msg.edit_text(
                    f"» {viv.mention} ᴀssɪsᴛᴀɴᴛ ɪs ᴍᴜᴛᴇᴅ ᴏɴ ᴠɪᴅᴇᴏᴄʜᴀᴛ,\n\nᴘʟᴇᴀsᴇ ᴜɴᴍᴜᴛᴇ {vi.mention} ᴏɴ ᴠɪᴅᴇᴏᴄʜᴀᴛ ᴀɴᴅ ᴛʀʏ ᴘʟᴀʏɪɴɢ ᴀɢᴀɪɴ."
                )
            except AlreadyJoinedError or ConnectionError:
                return await msg.edit_text(
                    f"ᴍᴜsɪᴄ ɪs ᴀʟʀᴇᴀᴅʏ ᴘʟᴀʏɪɴɢ ʙʏ ᴍᴀɪɴ ʙᴏᴛ ᴏʀ ᴀɴʏ ᴄʟᴏɴᴇᴅ ʙᴏᴛ"
                )

            except Exception as e:
                if "phone.CreateGroupCall" in str(e):
                    return await msg.edit_text(
                        "**» ɴᴏ ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ ғᴏᴜɴᴅ.**\n\nᴩʟᴇᴀsᴇ ᴍᴀᴋᴇ sᴜʀᴇ ʏᴏᴜ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ."
                    )
                else:
                    return await msg.edit_text(
                        f"sᴏᴍᴇ ᴇxᴄᴇᴘᴛɪᴏɴ ᴏᴄᴄᴜʀᴇᴅ ᴡʜᴇɴ ᴘʀᴏᴄᴇssɪɴɢ\n {e}"
                    )
            imgt = await gen_thumb(videoid)
            await stream_on(message.chat.id)
            await add_active_chat(message.chat.id)
            await message.reply_photo(
                photo=imgt,
                caption=f"**✮ 𝐒ʈᴧʀʈ𝛆ɗ 𝐒ʈʀ𝛆ɑɱɩŋʛ ✮**\n\n**✮ 𝐓ɩttɭ𝛆 ✮** [{title[:27]}](https://t.me/{viv.username}?start=info_{videoid})\n**✬ 𝐃ʋɽɑʈɩσŋ ✮** `{duration}` ᴍɪɴ\n**✭ 𝐁ɣ ✮** {ruser}",
                reply_markup=close_key,
            )
            await msg.delete()

        except Exception as e:
            await _clear_(message.chat.id)
            await pytgcalls.leave_call(message.chat.id)
            if "phone.CreateGroupCall" in str(e):
                return await msg.edit_text(
                    "**» ɴᴏ ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ ғᴏᴜɴᴅ.**\n\nᴩʟᴇᴀsᴇ ᴍᴀᴋᴇ sᴜʀᴇ ʏᴏᴜ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ."
                )
            else:
                return await msg.edit_text(
                    f"sᴏᴍᴇ ᴇxᴄᴇᴘᴛɪᴏɴ ᴏᴄᴄᴜʀᴇᴅ ᴡʜᴇɴ ᴘʀᴏᴄᴇssɪɴɢ\n {e}"
                )

    else:
        stream = MediaStream(file_path, audio_parameters=AudioQuality.HIGH)
        try:
            await pytgcalls.play(
                message.chat.id,
                stream,
            )

        except NoActiveGroupCall:
            return await msg.edit_text(
                "**» ɴᴏ ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ ғᴏᴜɴᴅ.**\n\nᴩʟᴇᴀsᴇ ᴍᴀᴋᴇ sᴜʀᴇ ʏᴏᴜ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ."
            )
        except TelegramServerError:
            return await msg.edit_text(
                "» ᴛᴇʟᴇɢʀᴀᴍ ɪs ʜᴀᴠɪɴɢ sᴏᴍᴇ ɪɴᴛᴇʀɴᴀʟ ᴘʀᴏʙʟᴇᴍs, ᴘʟᴇᴀsᴇ ʀᴇsᴛᴀʀᴛ ᴛʜᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ."
            )
        except UnMuteNeeded:
            return await msg.edit_text(
                f"» {viv.mention} ᴀssɪsᴛᴀɴᴛ ɪs ᴍᴜᴛᴇᴅ ᴏɴ ᴠɪᴅᴇᴏᴄʜᴀᴛ,\n\nᴘʟᴇᴀsᴇ ᴜɴᴍᴜᴛᴇ {vi.mention} ᴏɴ ᴠɪᴅᴇᴏᴄʜᴀᴛ ᴀɴᴅ ᴛʀʏ ᴘʟᴀʏɪɴɢ ᴀɢᴀɪɴ."
            )
        except AlreadyJoinedError or ConnectionError:
            return await msg.edit_text(
                f"ᴍᴜsɪᴄ ɪs ᴀʟʀᴇᴀᴅʏ ᴘʟᴀʏɪɴɢ ʙʏ ᴍᴀɪɴ ʙᴏᴛ ᴏʀ ᴀɴʏ ᴄʟᴏɴᴇᴅ ʙᴏᴛ"
            )
        except Exception as e:
            if "phone.CreateGroupCall" in str(e):
                return await msg.edit_text(
                    "**» ɴᴏ ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ ғᴏᴜɴᴅ.**\n\nᴩʟᴇᴀsᴇ ᴍᴀᴋᴇ sᴜʀᴇ ʏᴏᴜ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ."
                )
            else:
                logging.exception(e)
                return await msg.edit_text(
                    f"sᴏᴍᴇ ᴇxᴄᴇᴘᴛɪᴏɴ ᴏᴄᴄᴜʀᴇᴅ ᴡʜᴇɴ ᴘʀᴏᴄᴇssɪɴɢ\n {e}"
                )
        imgt = await gen_thumb(videoid)
        await stream_on(message.chat.id)
        await add_active_chat(message.chat.id)
        await message.reply_photo(
            photo=imgt,
            caption=f"**✮ 𝐒ʈᴧʀʈ𝛆ɗ 𝐒ʈʀ𝛆ɑɱɩŋʛ ✮**\n\n**✮ 𝐓ɩttɭ𝛆 ✮** [{title[:27]}](https://t.me/{viv.username}?start=info_{videoid})\n**✬ 𝐃ʋɽɑʈɩσŋ ✮** `{duration}` ᴍɪɴ\n**✭ 𝐁ɣ ✮** {ruser}",
            reply_markup=close_key,
        )
        await msg.delete()
