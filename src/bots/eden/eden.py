from discord.ext import commands

from cogs.GeneratorCog import GeneratorCog


class EdenBotCog(GeneratorCog):
    def __init__(self, bot: commands.bot) -> None:
        super().__init__(bot)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(EdenBotCog(bot))
