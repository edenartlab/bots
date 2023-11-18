from discord.ext import commands

from common.EdenCog import EdenCog


class EdenBotCog(EdenCog):
    def __init__(self, bot: commands.bot) -> None:
        super().__init__(bot)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(EdenBotCog(bot))
