from discord.ext import commands
from cogs.Eden2Cog import Eden2Cog


class EdenEden2Cog(Eden2Cog):
    def __init__(self, bot: commands.bot) -> None:
        super().__init__(bot)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(EdenEden2Cog(bot))
