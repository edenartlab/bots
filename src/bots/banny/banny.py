from discord.ext import commands

from common.EdenCog import EdenCog, LoraInput


class BannyBotCog(EdenCog):
    def __init__(self, bot: commands.bot) -> None:
        lora = LoraInput(
            lora_id="6509cd50762edacfc4ef8434",
            lora_strength=0.65,
            lora_trigger="banny",
            require_lora_trigger=True,
        )
        super().__init__(bot, lora)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(BannyBotCog(bot))
