import os
import random
import discord
from discord.ext import commands

from logos.scenarios import EdenAssistant

from common.discord import (
    get_source,
    is_mentioned,
    replace_bot_mention,
    replace_mentions_with_usernames,
)
from common.eden import generation_loop
from common.models import (
    EdenAssistantConfig,
    GenerationLoopInput,
    SignInCredentials,
    StableDiffusionConfig,
)

ALLOWED_CHANNELS = [int(c) for c in os.getenv("ALLOWED_CHANNELS", "").split(",")]

EDEN_API_URL = os.getenv("EDEN_API_URL")
EDEN_API_KEY = os.getenv("EDEN_API_KEY")
EDEN_API_SECRET = os.getenv("EDEN_API_SECRET")


class AssistantCog(commands.Cog):
    def __init__(
        self, bot: commands.bot, assistant_config: EdenAssistantConfig
    ) -> None:
        self.bot = bot
        self.eden_credentials = SignInCredentials(
            apiKey=EDEN_API_KEY, apiSecret=EDEN_API_SECRET
        )
        self.assistant = EdenAssistant(
            character_description=assistant_config.character_description,
            creator_prompt=assistant_config.creator_prompt,
            documentation_prompt=assistant_config.documentation_prompt,
            documentation=assistant_config.documentation,
            router_prompt=assistant_config.router_prompt,
        )

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

                response = self.assistant(
                    assistant_message, session_id=str(message.author.id)
                )
                print("rrrrr", response)

                reply = response["message"][:2000]
                reply_message = await message.reply(reply)

                # check if there is a config
                config = response["config"]
                if not config:
                    return

                mode = config.pop("generator")

                if "text_input" in config:
                    text_input = config["text_input"]
                elif "interpolation_texts" in config:
                    text_input = " to ".join(config["interpolation_texts"])
                else:
                    text_input = mode

                if "init_image_data" in config:
                    config["init_image_data"] = attachment_lookup_url.get(
                        config["init_image_data"]
                    )
                if "interpolation_init_images" in config:
                    config["interpolation_init_images"] = [
                        attachment_lookup_url.get(img)
                        for img in config["interpolation_init_images"]
                    ]

                config = StableDiffusionConfig(
                    generator_name=mode, seed=random.randint(1, 1e8), **config
                )

                source = get_source(ctx)

                is_video_request = mode in ["interpolate", "real2real"]

                start_bot_message = f"**{text_input}** - <@!{ctx.author.id}>\n"
                original_text = (
                    f"{reply[0:1950-len(start_bot_message)]}\n\n{start_bot_message}"
                )

                generation_loop_input = GenerationLoopInput(
                    api_url=EDEN_API_URL,
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
