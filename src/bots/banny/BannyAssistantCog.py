from pathlib import Path
from discord.ext import commands
from cogs.AssistantCog import AssistantCog
from common.models import BannyAssistantConfig


class BannyAssistantCog(AssistantCog):
    def __init__(self, bot: commands.bot) -> None:
        assistant_config = BannyAssistantConfig(
            character_description=self.load_prompt("character_description.txt"),
            creator_prompt=self.load_prompt("creator_prompt.txt"),
            documentation_prompt=self.load_prompt("documentation_prompt.txt"),
            documentation=self.load_prompt("documentation.txt"),
            router_prompt=self.load_prompt("router_prompt.txt"),
        )
        super().__init__(bot, assistant_config)

    def load_prompt(self, fname: str) -> str:
        path = Path(__file__).parent / "prompts" / fname
        with open(path, "r") as f:
            return f.read()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(BannyAssistantCog(bot))
