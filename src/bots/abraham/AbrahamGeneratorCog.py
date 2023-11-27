from discord.ext import commands

from cogs.GeneratorCog import GeneratorCog, LoraInput


class AbrahamGeneratorCog(GeneratorCog):
    def __init__(self, bot: commands.bot) -> None:
        lora = LoraInput(
            lora_id="6558ee435e91d48ad780de92",
            lora_strength=0.65,
            lora_trigger="Abraham",
            require_lora_trigger=True,
        )
        super().__init__(bot, lora)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AbrahamGeneratorCog(bot))
