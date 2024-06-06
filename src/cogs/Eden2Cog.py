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
# client.api_url = 'edenartlab--tasks-fastapi-app-dev.modal.run'
client.api_key = "2e4c65fb98622ca2aec8dae6ff07aae2eec3300aeab890e5"

thread_id = "664c3add9ab5c394b8fa2c7f"

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
        print("on... message ...", message.content)
        if (
            # message.channel.id not in ALLOWED_CHANNELS
            #or message.author.id == self.bot.user.id
            message.author.id == self.bot.user.id
            or message.author.bot
        ):
            return
        
        print("check if mention")
        trigger_reply = is_mentioned(message, self.bot.user)
        print("trig reply", trigger_reply)
        if not trigger_reply:
            return

        if message.channel.id != 1186378591118839808 and message.channel.id != 1006143747588898849:
            return
        
        print("got here..", message.content)
        global thread_id
        content = replace_bot_mention(message.content, only_first=True)
        content = replace_mentions_with_usernames(content, message.mentions)
        print("content", content)
        # Check if the message is a reply
        if message.reference:
            source_message = await message.channel.fetch_message(message.reference.message_id)
            # content = f"((Reply to {source_message.author.name}: {source_message.content[:120]} ...))\n\n{content}"
            content = f"((Reply to {source_message.author.name}: {source_message.content[:50]} ...))\n\n{content}"
            # TODO: extract urls don't shorten them

        chat_message = {
            "name": message.author.name,
            "content": content,
            "attachments": [attachment.url for attachment in message.attachments],
            "settings": {}
        }

        ctx = await self.bot.get_context(message)
        async with ctx.channel.typing():
            heartbeat_task = asyncio.create_task(self.heartbeat())
            try:
                print(chat_message)
                async for response in client.async_chat(chat_message, thread_id):
                    print(response)
                    error = response.get("error")
                    if error:
                        await reply(message, error)
                        continue
                    thread_id = response.get("thread_id") 
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
    content_chunks = [content[i:i+3980] for i in range(0, len(content), 3980)]
    for c, chunk in enumerate(content_chunks):
        await message.reply(chunk) if c == 0 else await message.channel.send(chunk)
