import os
import random
import discord
from datetime import datetime, timedelta
from attr import dataclass
from discord.ext import commands

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
    StableDiffusionConfig,
)

ALLOWED_CHANNELS = [int(c) for c in os.getenv("ALLOWED_CHANNELS", "").split(",")]

EDEN_API_URL = os.getenv("EDEN_API_URL")
LOGOS_URL = os.getenv("LOGOS_URL")
EDEN_FRONTEND_URL = EDEN_API_URL.replace("api", "app")
EDEN_API_KEY = os.getenv("EDEN_API_KEY")
EDEN_API_SECRET = os.getenv("EDEN_API_SECRET")
EDEN_CHARACTER_ID = os.getenv("EDEN_CHARACTER_ID")


@dataclass
class LoraInput:
    lora_id: str
    lora_strength: float
    lora_trigger: str
    require_lora_trigger: bool


class LogosCharacterCog(commands.Cog):
    def __init__(
        self,
        bot: commands.bot,
    ) -> None:
        print("LogosCharacterCog init...")
        self.bot = bot
        self.eden_credentials = SignInCredentials(
            apiKey=EDEN_API_KEY, apiSecret=EDEN_API_SECRET
        )
        self.characterId = EDEN_CHARACTER_ID

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> None:
        if (
            message.channel.id not in ALLOWED_CHANNELS
            or message.author.id == self.bot.user.id
            or message.author.bot
        ):
            return

        session_id = f'{message.channel.id}/{message.author.id}'
        prompt = self.message_preprocessor(message)
        attachment_urls = [attachment.url for attachment in message.attachments]

        cutoff = message.created_at - timedelta(minutes=90)
        conversation_history = await message.channel.history(after=cutoff).flatten()
        conversation = ""
        for message in conversation_history[-10:]:
            timestamp = message.created_at.strftime("%I:%M %p")
            author = message.author.name
            content = replace_mentions_with_usernames(
                message.content,
                message.mentions,
            )
            conversation += f"\n{author} — {timestamp}\n{content}\n"
            #if message.attachments:
        
        request = {
            "character_id": self.characterId,
            "session_id": session_id,
            "message": conversation,
            # "prompt": prompt,
            "attachments": attachment_urls,
        }

        trigger_reply = is_mentioned(message, self.bot.user)
        if not trigger_reply:
            trigger_reply = logos_think(LOGOS_URL, request)
        
        if trigger_reply:
            ctx = await self.bot.get_context(message)
            async with ctx.channel.typing():
                request["message"] = prompt
                response = logos_speak(LOGOS_URL, request)
                print("response")
                print(response)
                reply = response.get("message")
                reply_chunks = [reply[i:i+2000] for i in range(0, len(reply), 2000)]
                for chunk in reply_chunks:
                    reply_message = await message.reply(chunk)

                # check if there is a config
                config = response.get("config")

                if not config:
                    return

                if config.get("generator"):
                    mode = config.pop("generator")
                else:
                    return

                if config.get("text_input"):
                    text_input = config["text_input"]
                elif config.get("interpolation_texts"):
                    text_input = " to ".join(config["interpolation_texts"])
                else:
                    text_input = mode

                if not config.get("seed"):
                    config["seed"] = random.randint(1, 1e8)

                config = StableDiffusionConfig(generator_name=mode, **config)

                source = get_source(ctx)

                is_video_request = mode in ["interpolate", "real2real"]

                start_bot_message = f"**{text_input}** - <@!{ctx.author.id}>\n"
                original_text = (
                    f"{reply_message.content[0:1950-len(start_bot_message)]}\n\n{start_bot_message}"
                )

                generation_loop_input = GenerationLoopInput(
                    api_url=EDEN_API_URL,
                    frontend_url=EDEN_FRONTEND_URL,
                    message=reply_message,
                    start_bot_message=original_text,
                    source=source,
                    config=config,
                    prefer_gif=False,
                    is_video_request=is_video_request,
                )
                await generation_loop(
                    generation_loop_input, eden_credentials=self.eden_credentials
                )

    def message_preprocessor(self, message: discord.Message) -> str:
        message_content = replace_bot_mention(message.content, only_first=True)
        message_content = replace_mentions_with_usernames(
            message_content,
            message.mentions,
        )
        message_content = message_content.strip()
        return message_content

    def check_lora_trigger_provided(message: str, lora_trigger: str):
        return lora_trigger in message
