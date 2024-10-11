import os
import time
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

long_running_tools = ["txt2vid", "style_mixing", "img2vid", "vid2vid", "video_upscale", "vid2vid_sdxl", "lora_trainer", "animate_3D"]

# ALLOWED_CHANNELS = [int(c) for c in os.getenv("ALLOWED_CHANNELS", "").split(",")]
# EVE_AGENT_ID_ALL = os.getenv("EVE_AGENT_ID_ALL")
# EVE_AGENT_ID_PHOTO = os.getenv("EVE_AGENT_ID_PHOTO")

# EVE_AGENT_ID_ALL="66f1c7b4ee5c5f46bbfd3cb8"
# EVE_AGENT_ID_PHOTO="66f1c7b5ee5c5f46bbfd3cb9"


client = EdenClient(stage=False)
print(client)
discord_channels = client.get_discord_channels()
last_refresh_time = time.time()

from discord import ui, ButtonStyle

class MyView(ui.View):
    @ui.button(label="Click Me", style=ButtonStyle.green, custom_id="button_click")
    async def button_click(self, button: ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Button was clicked!", ephemeral=True)



video_tools = ["animate_3D", "txt2vid",  "img2vid", "vid2vid_sdxl", "style_mixing", "video_upscaler", "reel", "story", "lora_trainer"]
hour_timestamps = {}
day_timestamps = {}

HOUR_IMAGE_LIMIT = 50
HOUR_VIDEO_LIMIT = 10
DAY_IMAGE_LIMIT = 200
DAY_VIDEO_LIMIT = 40

def user_over_rate_limits(user_id):
    if user_id not in hour_timestamps:
        hour_timestamps[user_id] = []
    if user_id not in day_timestamps:
        day_timestamps[user_id] = []

    hour_timestamps[user_id] = [t for t in hour_timestamps[user_id] if time.time() - t["time"] < 3600]
    day_timestamps[user_id] = [t for t in day_timestamps[user_id] if time.time() - t["time"] < 86400]

    hour_video_tool_calls = len([t for t in hour_timestamps[user_id] if t["tool"] in video_tools])
    hour_image_tool_calls = len([t for t in hour_timestamps[user_id] if t["tool"] not in video_tools])

    day_video_tool_calls = len([t for t in day_timestamps[user_id] if t["tool"] in video_tools])
    day_image_tool_calls = len([t for t in day_timestamps[user_id] if t["tool"] not in video_tools])

    # print("hour_video_tool_calls", hour_video_tool_calls)
    # print("hour_image_tool_calls", hour_image_tool_calls)
    # print("day_video_tool_calls", day_video_tool_calls)
    # print("day_image_tool_calls", day_image_tool_calls)

    if hour_video_tool_calls >= HOUR_VIDEO_LIMIT or hour_image_tool_calls >= HOUR_IMAGE_LIMIT:
        return True
    if day_video_tool_calls >= DAY_VIDEO_LIMIT or day_image_tool_calls >= DAY_IMAGE_LIMIT:
        return True
    return False



class Eden2Cog(commands.Cog):
    def __init__(
        self,
        bot: commands.bot,
    ) -> None:
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> None:
        global discord_channels, last_refresh_time

        # Refresh discord_channels if it's been more than 5 minutes
        current_time = time.time()
        if current_time - last_refresh_time > 300:
            discord_channels = client.get_discord_channels()
            last_refresh_time = current_time

        print("on... message ...", message.content, "\n=============") 
        
        if (
            message.author.id == self.bot.user.id
            or message.author.bot
        ):
            return
        
        print("a2")
        
        is_dm = message.channel.type == discord.ChannelType.private
        if is_dm:
            thread_name = f"discord9-DM-{message.author.name}-{message.author.id}"
            dm_whitelist = [494760194203451393, 623923865864765452, 404322488215142410, 363287706798653441, 142466375024115712, 598627733576089681, 551619012140990465]
            if message.author.id not in dm_whitelist:
                return
        else:
            thread_name = f"discord9-{message.guild.name}-{message.channel.id}-{message.author.id}"
            trigger_reply = is_mentioned(message, self.bot.user)
            if not trigger_reply:
                return
            print("a3")
            print("message.channel.id", message.channel.id)
            print("discord_channels", discord_channels)
            
            if str(message.channel.id) not in discord_channels:
                return
        if user_over_rate_limits(message.author.id):
            await reply(message, "I'm sorry, you've hit your rate limit. Please try again a bit later!")
            return
        print("a4")
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
            thread_id = client.get_or_create_thread(thread_name)
            #agent_id = EVE_AGENT_ID_PHOTO if message.channel.id == 1288181593051107490 else EVE_AGENT_ID_ALL
            #agent_id = EVE_AGENT_ID_PHOTO if message.channel.id == 1288181593051107490 else EVE_AGENT_ID_ALL
            answered = False
            channel_id = str(message.channel.id)

            async for response in client.async_discord_chat(chat_message, thread_id, channel_id):
                print("THE RESPONSE", response)
                if 'error' in response:
                    error_message = response.get("error")
                    await reply(message, f"Error: {error_message}")
                    continue

                if not response.get("message"):
                    continue

                response = json.loads(response.get("message"))
                content = response.get("content", "")
                tool_results = response.get("tool_results")
                
                if tool_results:
                    for t in tool_results:
                        print("tool result")
                        hour_timestamps[message.author.id].append({"time": time.time(), "tool": t["name"]})
                        day_timestamps[message.author.id].append({"time": time.time(), "tool": t["name"]}) 
                        print("tool called", t["name"])
                        print(hour_timestamps[message.author.id])

                if content:
                    if not answered:
                        await reply(message, content)
                    else:
                        await send(message, content)
                    answered = True


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

async def send(message, content):
    content_chunks = [content[i:i+1980] for i in range(0, len(content), 1980)]
    for c, chunk in enumerate(content_chunks):
        await message.channel.send(chunk)


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
