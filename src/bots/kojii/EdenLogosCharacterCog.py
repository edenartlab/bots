from discord.ext import commands
from cogs.LogosCharacterCog import LogosCharacterCog


GUILD_ID = 1128729869535150260

welcome_message = """🎨 Welcome to kojii.ai Discord! 🤖✨

Hello **{name}** and welcome to our creative space! 🚀 I'm excited to have you here as part of our community of art enthusiasts and tech explorers.

🌟 Dive into our various channels. Introduce yourself in https://discord.com/channels/1128729869535150260/1203819263731834961 and head over to https://discord.com/channels/1128729869535150260/1203819229066043433 for a relaxed conversation. 

💬 Our team is here to help! If you have any questions, ideas, or need assistance, feel free to reach out to us in https://discord.com/channels/1128729869535150260/1203819834836656128. 

🎙️ This Discord is a hub for creativity! Share your thoughts, ideas, or even your latest artworks in https://discord.com/channels/1128729869535150260/1203819881481506876.

🤖 Ready to unleash your creativity? Head over to your favorite artist channel and play with the models. Don't forget to share your masterpieces with the community!

🌈 Enjoy Your Stay:
We hope you have an incredible time exploring, creating, and connecting. Thank you for joining!
"""


class EdenLogosCharacterCog(LogosCharacterCog):
    def __init__(self, bot: commands.bot) -> None:
        super().__init__(bot)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != GUILD_ID:
            return
        print(f"{member} has joined the guild id: {member.guild.id}")
        await member.send(welcome_message.format(name=member.name))


def setup(bot: commands.Bot) -> None:
    bot.add_cog(EdenLogosCharacterCog(bot))
