from discord.ext import commands
from cogs.LogosCharacterCog import LogosCharacterCog


class EdenEden2Cog(LogosCharacterCog):
    def __init__(self, bot: commands.bot) -> None:
        super().__init__(bot)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(LogosCharacterCog(bot))
