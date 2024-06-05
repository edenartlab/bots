import os
import random
import discord
import json
from datetime import datetime, timedelta
from attr import dataclass
from discord.ext import commands

from eden import EdenClient

from common.discord import (
    get_source,
    is_mentioned,
    replace_bot_mention,
    replace_mentions_with_usernames,
)
from common.eden import (
    generation_loop, 
    get_assistant,
)
from common.logos import (
    logos_think, 
    logos_speak,
)
from common.models import (
    GenerationLoopInput,
    SignInCredentials,
    EdenConfig,
)

# ALLOWED_CHANNELS = [int(c) for c in os.getenv("ALLOWED_CHANNELS", "").split(",")]
EDEN_CHARACTER_ID = os.getenv("EDEN_CHARACTER_ID")

client = EdenClient()
client.api_key = "2e4c65fb98622ca2aec8dae6ff07aae2eec3300aeab890e5"
print(client.api_url)
thread_id = "665161a77df49de2c24fc225"

import asyncio

class Eden2Cog(commands.Cog):
    def __init__(
        self,
        bot: commands.bot,
    ) -> None:
        self.bot = bot
        self.characterId = EDEN_CHARACTER_ID

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> None:
        print("ok???")
        print("ON MESSAGE", message.content)
        if (
            # message.channel.id not in ALLOWED_CHANNELS
            #or message.author.id == self.bot.user.id
            message.author.id == self.bot.user.id
            or message.author.bot
        ):
            return
        
        trigger_reply = is_mentioned(message, self.bot.user)
        if not trigger_reply:
            return

        if message.channel.id != 1186378591118839808 and message.channel.id != 1006143747588898849:
            return
        
        global thread_id
        content = replace_bot_mention(message.content, only_first=True)
        content = replace_mentions_with_usernames(content, message.mentions)

        # Check if the message is a reply
        if message.reference:
            source_message = await message.channel.fetch_message(message.reference.message_id)
            content = f"((Reply to {source_message.author.name}: {source_message.content[:120]} ...))\n\n{content}"
            # TODO: extract urls don't shorten them

        chat_message = {
            "name": message.author.name,
            "content": content,
            "attachments": [attachment.url for attachment in message.attachments],
            "settings": {}
        }
        print("THE CHAT MESSAGE", chat_message)

        ctx = await self.bot.get_context(message)
        print("ctx 1")
        async with ctx.channel.typing():
            print("ctx 2")
            print("TO THE URL", client.api_url)

            heartbeat_task = asyncio.create_task(self.heartbeat())

            try:                    
                async for response in client.async_chat(chat_message, thread_id):
                    print("ctx 3")
                    print("-----------------")
                    print(response)
                    error = response.get("error")
                    print("ERROR", error)
                    if error:
                        await reply(message, error)
                        continue
                    thread_id = response.get("task_id") 
                    msg = json.loads(response.get("message"))
                    content = msg.get("content")
                    if content:
                        await reply(message, content)
            finally:
                # Cancel the heartbeat task when the chat is done
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    print("Heartbeat stopped.")

    async def heartbeat(self):
        while True:
            print("Heartbeat: The chat is still running.")
            await asyncio.sleep(2)


async def reply(message, content):
    content_chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
    for c, chunk in enumerate(content_chunks):
        await message.reply(chunk) if c == 0 else await message.channel.send(chunk)
