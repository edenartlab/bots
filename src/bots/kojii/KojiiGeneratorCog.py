from discord.ext import commands

from cogs.GeneratorCog import GeneratorCog, LoraInput


class KojiiGeneratorCog(GeneratorCog):
    def __init__(self, bot: commands.bot) -> None:
        lora = LoraInput(
            lora_id="65642f6a730b5e00f6f243d6",
            lora_strength=0.65,
            lora_trigger="kojii",
            require_lora_trigger=True,
        )
        super().__init__(bot, lora)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(KojiiGeneratorCog(bot))
