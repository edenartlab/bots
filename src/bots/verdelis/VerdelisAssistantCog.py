from pathlib import Path
from discord.ext import commands
from cogs.AssistantCog import AssistantCog, LoraInput
from common.models import EdenAssistantConfig


class VerdelisAssistantCog(AssistantCog):
    def __init__(self, bot: commands.bot) -> None:
        lora = LoraInput(
            lora_id="656434c2730b5e00f6004bae",
            lora_strength=0.65,
            lora_trigger="verdelis",
            require_lora_trigger=True,
        )
        assistant_config = EdenAssistantConfig(
            character_description=self.load_prompt("character_description.txt"),
            creator_prompt=self.load_prompt("creator_prompt.txt"),
            documentation_prompt=self.load_prompt("documentation_prompt.txt"),
            documentation=self.load_prompt("documentation.txt"),
            router_prompt=self.load_prompt("router_prompt.txt"),
        )
        super().__init__(bot, assistant_config, lora)

    def load_prompt(self, fname: str) -> str:
        path = Path(__file__).parent / "prompts" / fname
        with open(path, "r") as f:
            return f.read()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(VerdelisAssistantCog(bot))
