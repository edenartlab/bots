from discord.ext import commands
from cogs.CharacterCog import CharacterCog


class BannyCharacterCog(CharacterCog):
    def __init__(self, bot: commands.bot) -> None:
        super().__init__(bot)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(BannyCharacterCog(bot))
