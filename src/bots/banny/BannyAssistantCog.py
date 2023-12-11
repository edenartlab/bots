from pathlib import Path
from discord.ext import commands
from cogs.AssistantCog import AssistantCog


class BannyAssistantCog(AssistantCog):
    def __init__(self, bot: commands.bot) -> None:
        super().__init__(bot)

    def load_prompt(self, fname: str) -> str:
        path = Path(__file__).parent / "prompts" / fname
        with open(path, "r") as f:
            return f.read()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(BannyAssistantCog(bot))
