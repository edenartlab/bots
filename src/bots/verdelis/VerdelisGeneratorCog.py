from discord.ext import commands

from cogs.GeneratorCog import GeneratorCog, LoraInput


class VerdelisGeneratorCog(GeneratorCog):
    def __init__(self, bot: commands.bot) -> None:
        lora = LoraInput(
            lora_id="656434c2730b5e00f6004bae",
            lora_strength=0.65,
            lora_trigger="verdelis",
            require_lora_trigger=True,
        )
        super().__init__(bot, lora)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(VerdelisGeneratorCog(bot))
