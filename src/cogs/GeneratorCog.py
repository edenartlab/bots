import os
import random
from typing import Optional
from attr import dataclass
import discord
from discord.ext import commands

from common.discord import (
    get_source,
)
from common.eden import (
    generation_loop,
)
from common.models import (
    GenerationLoopInput,
    SignInCredentials,
    StableDiffusionConfig,
)

ALLOWED_GUILDS = [g for g in os.getenv("ALLOWED_GUILDS", "").split(",")] or []
ALLOWED_GUILDS = [int(g) for g in ALLOWED_GUILDS]
ALLOWED_GUILDS_TEST = [g for g in os.getenv("ALLOWED_GUILDS_TEST", "").split(",")] or []
ALLOWED_GUILDS_TEST = [int(g) for g in ALLOWED_GUILDS_TEST]
ALLOWED_CHANNELS = [int(c) for c in os.getenv("ALLOWED_CHANNELS", "").split(",")]

EDEN_API_URL = os.getenv("EDEN_API_URL")
EDEN_FRONTEND_URL = EDEN_API_URL.replace("api", "app")
EDEN_API_KEY = os.getenv("EDEN_API_KEY")
EDEN_API_SECRET = os.getenv("EDEN_API_SECRET")


@dataclass
class LoraInput:
    lora_id: str
    lora_strength: float
    lora_trigger: str
    require_lora_trigger: bool


class GeneratorCog(commands.Cog):
    def __init__(self, bot: commands.bot, lora: Optional[LoraInput] = None) -> None:
        self.bot = bot
        self.eden_credentials = SignInCredentials(
            apiKey=EDEN_API_KEY, apiSecret=EDEN_API_SECRET
        )
        self.lora = lora

    @commands.slash_command(guild_ids=ALLOWED_GUILDS_TEST)
    async def test(
        self,
        ctx,
    ):
        print("Received test")

        config = StableDiffusionConfig(
            generator_name="test",
        )

        start_bot_message = f"**Testing** - <@!{ctx.author.id}>\n"
        await ctx.respond("Starting to create...")
        message = await ctx.channel.send(start_bot_message)

        source = get_source(ctx)

        generation_loop_input = GenerationLoopInput(
            api_url=EDEN_API_URL,
            frontend_url=EDEN_FRONTEND_URL,
            message=message,
            start_bot_message=start_bot_message,
            source=source,
            config=config,
            is_video_request=False,
        )
        await generation_loop(
            generation_loop_input, eden_credentials=self.eden_credentials
        )

    @commands.slash_command(guild_ids=ALLOWED_GUILDS)
    async def create(
        self,
        ctx,
        text_input: discord.Option(str, description="Prompt", required=True),
        aspect_ratio: discord.Option(
            str,
            choices=[
                discord.OptionChoice(name="square", value="square"),
                discord.OptionChoice(name="landscape", value="landscape"),
                discord.OptionChoice(name="portrait", value="portrait"),
            ],
            required=False,
            default="square",
        ),
    ):
        print("Received create:", text_input)

        if not self.perm_check(ctx):
            await ctx.respond("This command is not available in this channel.")
            return

        # TODO: Content filter
        # if settings.CONTENT_FILTER_ON:
        #     if not OpenAIGPT3LanguageModel.content_safe(text_input):
        #         await ctx.respond(
        #             f"Content filter triggered, <@!{ctx.author.id}>. Please don't make me draw that. If you think it was a mistake, modify your prompt slightly and try again.",
        #         )
        #         return

        source = get_source(ctx)
        large, fast = False, False
        width, height, upscale_f = self.get_dimensions(aspect_ratio, large)
        steps = 15 if fast else 35

        config = StableDiffusionConfig(
            generator_name="create",
            text_input=text_input,
            width=width,
            height=height,
            steps=steps,
            guidance_scale=8,
            upscale_f=upscale_f,
            seed=random.randint(1, 1e8),
        )

        config = self.add_lora(config)
        print(config)

        start_bot_message = f"**{text_input}** - <@!{ctx.author.id}>\n"
        await ctx.respond("Starting to create...")
        message = await ctx.channel.send(start_bot_message)

        generation_loop_input = GenerationLoopInput(
            api_url=EDEN_API_URL,
            frontend_url=EDEN_FRONTEND_URL,
            message=message,
            start_bot_message=start_bot_message,
            source=source,
            config=config,
            is_video_request=False,
        )
        await generation_loop(
            generation_loop_input, eden_credentials=self.eden_credentials
        )

    @commands.slash_command(guild_ids=ALLOWED_GUILDS)
    async def remix(
        self,
        ctx,
        image1: discord.Option(
            discord.Attachment, description="Image to remix", required=True
        ),
    ):
        print("Received remix:", image1)

        if not self.perm_check(ctx):
            await ctx.respond("This command is not available in this channel.")
            return

        if not image1:
            await ctx.respond("Please provide an image to remix.")
            return

        source = get_source(ctx)

        steps = 50
        width, height = 1024, 1024

        config = StableDiffusionConfig(
            generator_name="remix",
            text_input="remix",
            init_image_data=image1.url,
            init_image_strength=0.125,
            width=width,
            height=height,
            steps=steps,
            guidance_scale=8,
            seed=random.randint(1, 1e8),
        )

        config = self.add_lora(config)

        start_bot_message = f"**Remix** by <@!{ctx.author.id}>\n"
        await ctx.respond("Remixing...")
        message = await ctx.channel.send(start_bot_message)

        generation_loop_input = GenerationLoopInput(
            api_url=EDEN_API_URL,
            frontend_url=EDEN_FRONTEND_URL,
            message=message,
            start_bot_message=start_bot_message,
            source=source,
            config=config,
            is_video_request=False,
            prefer_gif=False,
        )
        await generation_loop(
            generation_loop_input, eden_credentials=self.eden_credentials
        )

    @commands.slash_command(guild_ids=ALLOWED_GUILDS)
    async def real2real(
        self,
        ctx,
        image1: discord.Option(
            discord.Attachment, description="First image", required=True
        ),
        image2: discord.Option(
            discord.Attachment, description="Second image", required=True
        ),
    ):
        if not self.perm_check(ctx):
            await ctx.respond("This command is not available in this channel.")
            return

        source = get_source(ctx)

        if not (image1 and image2):
            await ctx.respond("Please provide two images to interpolate between.")
            return

        interpolation_init_images = [image1.url, image2.url]

        interpolation_seeds = [
            random.randint(1, 1e8) for _ in interpolation_init_images
        ]
        n_frames = 50
        steps = 40
        width, height = 768, 768

        config = StableDiffusionConfig(
            generator_name="real2real",
            stream=True,
            stream_every=1,
            text_input="real2real",
            interpolation_seeds=interpolation_seeds,
            interpolation_init_images=interpolation_init_images,
            interpolation_init_images_use_img2txt=True,
            n_frames=n_frames,
            loop=True,
            smooth=True,
            n_film=1,
            width=width,
            height=height,
            steps=steps,
            guidance_scale=6.5,
            seed=random.randint(1, 1e8),
            interpolation_init_images_min_strength=0.3,  # a higher value will make the video smoother, but allows less visual change / journey
        )

        config = self.add_lora(config)

        start_bot_message = f"**Real2Real** by <@!{ctx.author.id}>\n"
        await ctx.respond("Lerping...")
        message = await ctx.channel.send(start_bot_message)

        generation_loop_input = GenerationLoopInput(
            api_url=EDEN_API_URL,
            frontend_url=EDEN_FRONTEND_URL,
            message=message,
            start_bot_message=start_bot_message,
            source=source,
            config=config,
            is_video_request=True,
            prefer_gif=False,
        )
        await generation_loop(
            generation_loop_input, eden_credentials=self.eden_credentials
        )

    @commands.slash_command(guild_ids=ALLOWED_GUILDS)
    async def lerp(
        self,
        ctx,
        text_input1: discord.Option(str, description="First prompt", required=True),
        text_input2: discord.Option(str, description="Second prompt", required=True),
        aspect_ratio: discord.Option(
            str,
            choices=[
                discord.OptionChoice(name="square", value="square"),
                discord.OptionChoice(name="landscape", value="landscape"),
                discord.OptionChoice(name="portrait", value="portrait"),
            ],
            required=False,
            default="square",
        ),
    ):
        print("Received lerp:", text_input1, text_input2)

        if not self.perm_check(ctx):
            await ctx.respond("This command is not available in this channel.")
            return

        # if settings.CONTENT_FILTER_ON:
        #     if not OpenAIGPT3LanguageModel.content_safe(
        #         text_input1,
        #     ) or not OpenAIGPT3LanguageModel.content_safe(text_input2):
        #         await ctx.respond(
        #             f"Content filter triggered, <@!{ctx.author.id}>. Please don't make me draw that. If you think it was a mistake, modify your prompt slightly and try again.",
        #         )
        #         return

        source = get_source(ctx)

        interpolation_texts = [text_input1, text_input2]
        interpolation_seeds = [random.randint(1, 1e8) for _ in interpolation_texts]
        n_frames = 50
        steps = 40
        width, height, upscale_f = self.get_video_dimensions(aspect_ratio, False)

        config = StableDiffusionConfig(
            generator_name="interpolate",
            stream=True,
            stream_every=1,
            text_input=text_input1,
            interpolation_texts=interpolation_texts,
            interpolation_seeds=interpolation_seeds,
            n_frames=n_frames,
            smooth=True,
            loop=True,
            n_film=1,
            width=width,
            height=height,
            sampler="euler",
            steps=steps,
            guidance_scale=8,
            seed=random.randint(1, 1e8),
        )

        config = self.add_lora(config)

        start_bot_message = (
            f"**{text_input1}** to **{text_input2}** - <@!{ctx.author.id}>\n"
        )
        await ctx.respond("Lerping...")
        message = await ctx.channel.send(start_bot_message)

        generation_loop_input = GenerationLoopInput(
            api_url=EDEN_API_URL,
            frontend_url=EDEN_FRONTEND_URL,
            message=message,
            start_bot_message=start_bot_message,
            source=source,
            config=config,
            is_video_request=True,
            prefer_gif=False,
        )
        await generation_loop(
            generation_loop_input, eden_credentials=self.eden_credentials
        )

    def get_video_dimensions(self, aspect_ratio):
        if aspect_ratio == "square":
            width, height = 1024, 1024
        elif aspect_ratio == "landscape":
            width, height = 1280, 768
        elif aspect_ratio == "portrait":
            width, height = 768, 1280
        upscale_f = 1.0
        return width, height, upscale_f

    def get_dimensions(self, aspect_ratio, large):
        if aspect_ratio == "square":
            width, height = 1024, 1024
        elif aspect_ratio == "landscape":
            width, height = 1280, 768
        elif aspect_ratio == "portrait":
            width, height = 768, 1280
        upscale_f = 1.4 if large else 1.0
        return width, height, upscale_f

    def perm_check(self, ctx):
        if ctx.channel.id not in ALLOWED_CHANNELS:
            return False
        return True

    def add_lora(self, config: StableDiffusionConfig):
        if self.lora:
            config.lora = self.lora.lora_id
            config.lora_strength = self.lora.lora_strength
        return config

    def check_lora_trigger_provided(message: str, lora_trigger: str):
        return lora_trigger in message
