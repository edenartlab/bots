from discord.ext import commands
from cogs.LogosCharacterCog import LogosCharacterCog


class EdenLogosCharacterCog(LogosCharacterCog):
    def __init__(self, bot: commands.bot) -> None:
        super().__init__(bot)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f"{member} has joined the guild id: {member.guild.id}")
        await member.send("Welcome to the server! Please read the rules and enjoy your stay!")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(EdenLogosCharacterCog(bot))
