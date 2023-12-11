from discord.ext import commands
from cogs.AssistantCog import AssistantCog


class EdenAssistantCog(AssistantCog):
    def __init__(self, bot: commands.bot) -> None:
        super().__init__(bot)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(EdenAssistantCog(bot))
