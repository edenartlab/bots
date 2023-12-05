from discord.ext import commands

from cogs.GeneratorCog import GeneratorCog, LoraInput


class SwolesGeneratorCog(GeneratorCog):
    def __init__(self, bot: commands.bot) -> None:
        lora = LoraInput(
            lora_id="65642e86730b5e00f6f17008",
            lora_strength=0.65,
            lora_trigger="banny",
            require_lora_trigger=True,
        )
        #super().__init__(bot, lora)
        super().__init__(bot)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(SwolesGeneratorCog(bot))
