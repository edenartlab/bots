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

long_running_tools = ["txt2vid", "style_mixing", "img2vid", "vid2vid", "video_upscale", "vid2vid_sdxl"]

# ALLOWED_CHANNELS = [int(c) for c in os.getenv("ALLOWED_CHANNELS", "").split(",")]
EDEN_CHARACTER_ID = os.getenv("EDEN_CHARACTER_ID")

client = EdenClient()
print("client", client.api_key)


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

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> None:
        print("on... message ...", message.content)
        
        if (
            message.author.id == self.bot.user.id
            or message.author.bot
        ):
            return
        
        is_dm = message.channel.type == discord.ChannelType.private
        if is_dm:
            thread_name = f"discord4-DM-{message.author.name}-{message.author.id}"
            dm_whitelist = [494760194203451393, 623923865864765452, 404322488215142410, 363287706798653441, 142466375024115712, 598627733576089681, 551619012140990465]
            if message.author.id not in dm_whitelist:
                return
        else:
            thread_name = f"discord4-{message.guild.name}-{message.channel.id}-{message.author.id}"
            trigger_reply = is_mentioned(message, self.bot.user)
            if not trigger_reply:
                return
            if message.channel.id != 1186378591118839808 and message.channel.id != 1006143747588898849:
                return
        
        content = replace_bot_mention(message.content, only_first=True)
        content = replace_mentions_with_usernames(content, message.mentions)
        
        # Check if the message is a reply
        if message.reference:
            source_message = await message.channel.fetch_message(message.reference.message_id)
            # content = f"((Reply to {source_message.author.name}: {source_message.content[:120]} ...))\n\n{content}"
            # content = f"(Reply to {source_message.author.name}: {source_message.content[:50]} ...))\n\n{content}"
            content = f"(Replying to message: {source_message.content[:100]} ...)\n\n{content}"
            # TODO: extract urls don't shorten them

        chat_message = {
            "name": message.author.name,
            "content": content,
            "attachments": [attachment.url for attachment in message.attachments],
            "settings": {}
        }
        print("chat message", chat_message)

        ctx = await self.bot.get_context(message)
        async with ctx.channel.typing():
            import random
            ran = random.randint(1, 10000)
            print(ran, content)
            # print(chat_message)

            print("look for", f"discord4-{message.channel.id}-{message.author.id}")
            thread_id = client.get_or_create_thread(thread_name)
            print("thread id", thread_id)

            answered = False
            async for response in client.async_chat(chat_message, thread_id):
                print(ran, response)
                if 'error' in response:
                    error_message = response.get("error")
                    await reply(message, f"Error: {error_message}")
                    continue
                print("response to json", response)
                response = json.loads(response.get("message"))
                content = response.get("content")
                # tool_calls = response.get("tool_calls")
                # if tool_calls:
                #     tool_name = tool_calls[0].get("function").get("name")
                #     if tool_name in long_running_tools and not answered:
                #         args = json.loads(tool_calls[0].get("function").get("arguments"))
                #         prompt = args.get("prompt")
                #         if prompt:
                #             await reply(message, f"Running {tool_name}: {prompt}. Please wait...")
                #         else:
                #             await reply(message, f"Running {tool_name}. Please wait...")
                        
                if content:
                    # answered = True
                    await reply(message, content)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        #if member.guild.id not in [1006143747588898846, 573691888050241543]:
        if member.guild.id not in [1006143747588898846]:
            return
        print(f"{member} has joined the guild id: {member.guild.id}")
        await member.send(welcome_message.format(name=member.name))


async def reply(message, content):
    content_chunks = [content[i:i+1980] for i in range(0, len(content), 1980)]
    for c, chunk in enumerate(content_chunks):
        await message.reply(chunk) if c == 0 else await message.channel.send(chunk)



welcome_message = """Welcome to Eden, {name}!!!

My name is Eve, and I'm so excited to have you here as part of our community of art enthusiasts and tech explorers.

Some things you can do in our Discord:

🌟 Introduce yourself in https://discord.com/channels/573691888050241543/589021495054041099 and go to https://discord.com/channels/573691888050241543/573691888482123778 for general chat. 

💬 If you have any questions, ideas, or need assistance, we are here to help you. Feel free to share your issues with us at https://discord.com/channels/573691888050241543/1105265688169422888. 

🎙️ Share your art with us on https://discord.com/channels/573691888050241543/1234589555538006107.

📢 Follow announcements and updates from the Eden team at https://discord.com/channels/573691888050241543/897336553754472448.

🤖 Talk to me!! You can converse with me and make art with me at https://discord.com/channels/573691888050241543/11863785911188398081234589555538006107.

We hope you have an incredible time exploring, creating, and connecting. Thank you for joining!
"""
