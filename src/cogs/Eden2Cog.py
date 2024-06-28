import os
import asyncio
import discord
import json
from datetime import datetime, timedelta
from attr import dataclass
from discord.ext import commands

from eden import EdenClient

from common.discord import (
    is_mentioned,
    replace_bot_mention,
    replace_mentions_with_usernames,
)

# ALLOWED_CHANNELS = [int(c) for c in os.getenv("ALLOWED_CHANNELS", "").split(",")]
EDEN_CHARACTER_ID = os.getenv("EDEN_CHARACTER_ID")

client = EdenClient()


from discord import ui, ButtonStyle

class MyView(ui.View):
    @ui.button(label="Click Me", style=ButtonStyle.green, custom_id="button_click")
    async def button_click(self, button: ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Button was clicked!", ephemeral=True)





class Eden2Cog(commands.Cog):
    def __init__(
        self,
        bot: commands.bot,
    ) -> None:
        self.bot = bot
        self.characterId = EDEN_CHARACTER_ID
        self.thread_id = client.get_or_create_thread("discord-test3")
        print("thread id", self.thread_id)

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> None:
        print("on... message ...", message.content)
        if (
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
            print(chat_message)
            async for response in client.async_chat(chat_message, self.thread_id):
                print(response)
                error = response.get("error")
                if error:
                    await reply(message, error)
                    continue
                response = json.loads(response.get("message"))
                content = response.get("content")
                tool_calls = response.get("tool_calls")
                if tool_calls:
                    tool_name = tool_calls[0].get("function").get("name")
                    if tool_name in ["txt2vid", "style_mixing", "img2vid", "vid2vid", "video_upscale"]:
                        args = json.loads(tool_calls[0].get("function").get("arguments"))
                        prompt = args.get("prompt")
                        content = f"Running {tool_name}: {prompt}. Please wait..."
                        await reply(message, content)
                if content:
                    await reply(message, content)

async def reply(message, content):
    content_chunks = [content[i:i+3980] for i in range(0, len(content), 3980)]
    for c, chunk in enumerate(content_chunks):
        await message.reply(chunk) if c == 0 else await message.channel.send(chunk)


