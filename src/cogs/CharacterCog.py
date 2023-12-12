import os
import random
import discord
from attr import dataclass
from discord.ext import commands

from common.discord import (
    get_source,
    is_mentioned,
    replace_bot_mention,
    replace_mentions_with_usernames,
)
from common.eden import generation_loop, get_assistant
from common.models import (
    GenerationLoopInput,
    SignInCredentials,
    StableDiffusionConfig,
)

ALLOWED_CHANNELS = [int(c) for c in os.getenv("ALLOWED_CHANNELS", "").split(",")]

EDEN_API_URL = os.getenv("EDEN_API_URL")
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


class CharacterCog(commands.Cog):
    def __init__(
        self,
        bot: commands.bot,
    ) -> None:
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

        trigger_reply = is_mentioned(message, self.bot.user)

        if trigger_reply:
            ctx = await self.bot.get_context(message)
            async with ctx.channel.typing():
                prompt = self.message_preprocessor(message)

                attachment_urls = [attachment.url for attachment in message.attachments]
                attachment_lookup_file = {
                    url: f"/files/image{i+1}.jpeg"
                    for i, url in enumerate(attachment_urls)
                }
                attachment_lookup_url = {
                    v: k for k, v in attachment_lookup_file.items()
                }
                attachment_files = [
                    attachment_lookup_file[url] for url in attachment_urls
                ]
                assistant_message = {
                    "prompt": prompt,
                    "attachments": attachment_files,
                }

                assistant, concept = get_assistant(
                    api_url=EDEN_API_URL,
                    character_id=self.characterId,
                    credentials=self.eden_credentials,
                )

                response = assistant(
                    assistant_message, session_id=str(message.author.id)
                )
                reply = response.get("message")[:2000]
                reply_message = await message.reply(reply)

                # check if there is a config
                config = response.get("config")

                if not config:
                    return

                mode = config.pop("generator")

                if config.get("text_input"):
                    text_input = config["text_input"]
                elif config.get("interpolation_texts"):
                    text_input = " to ".join(config["interpolation_texts"])
                else:
                    text_input = mode

                if config.get("init_image"):
                    config["init_image"] = attachment_lookup_url.get(
                        config["init_image"]
                    )
                if config.get("interpolation_init_images"):
                    config["interpolation_init_images"] = [
                        attachment_lookup_url.get(img)
                        for img in config["interpolation_init_images"]
                    ]
                if not config.get("seed"):
                    config["seed"] = random.randint(1, 1e8)

                config = StableDiffusionConfig(generator_name=mode, **config)

                config = self.add_lora(config, concept)

                source = get_source(ctx)

                is_video_request = mode in ["interpolate", "real2real"]

                start_bot_message = f"**{text_input}** - <@!{ctx.author.id}>\n"
                original_text = (
                    f"{reply[0:1950-len(start_bot_message)]}\n\n{start_bot_message}"
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

    def add_lora(self, config: StableDiffusionConfig, concept: str):
        if concept:
            config.lora = concept
            config.lora_strength = 0.6
        return config

    def check_lora_trigger_provided(message: str, lora_trigger: str):
        return lora_trigger in message
