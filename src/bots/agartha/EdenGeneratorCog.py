from discord.ext import commands
from cogs.CharacterGeneratorCog import CharacterGeneratorCog


class EdenCharacterGeneratorCog(CharacterGeneratorCog):
    def __init__(self, bot: commands.bot) -> None:
        super().__init__(bot)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(EdenCharacterGeneratorCog(bot))
