import sqlite3
import discord
import psutil
import os
from discord.ext import commands
from utils import default


def format_for_embed(tuple):
    return '\n'.join([f"`{command}`" + " " + argument for command, argument in tuple])


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command()
    async def oldhelp(self, ctx):
        """
        Lists all commands.
        """
        embed = discord.Embed(title="Slant Commands", color=discord.Color.blue())

        # moderation = ["ban", "kick", "find", "massban", "mute", "nickname", "prune", "unban", "unmute"]
        # embed.add_field(
        #     name="Moderation",
        #     value=format_for_embed(moderation),
        #     inline= False
        #     )

        Info = [
            ("avatar", "member"),
            ("avatarhistory", "member"),
            ("banner", "member"),
            ("userinfo", "member"),
            ("serverinfo", " "),
            ("avatar", "member"),
            ("about", " "),
            ("names", "member"),
            ("invite", " "),
            ("country", "country"),
            ("covid", "country"),
            ("ping", " "),
            ("roles", " "),
            ("recent", " ")
        ]
        embed.add_field(
            name="Info",
            value=format_for_embed(Info),
            inline=False
        )

        Leaderboards = [
            ("leaderboard", "member"),
            ("userpeak", "member"),
            ("serverpeak", "member"),
            ("age", " "),
            ("crowns", "member"),
            ("mention", "member")
        ]
        embed.add_field(
            name="Leaderboard",
            value=format_for_embed(Leaderboards)
        )

        Vocabulary = [
            ("vocab", " "),
            ("vocabuser", "member"),
            ("said", "member"),
            ("wordcloud", "member"),
            ("wordcloudserver", "min word length")
        ]
        embed.add_field(
            name="Vocabulary",
            value=format_for_embed(Vocabulary),
            inline=False
        )

        VC = [
            ("massmove", "channel"),
            ("massmoveall", "channel")
        ]
        embed.add_field(
            name="VC",
            value=format_for_embed(VC),
            inline=False
        )

        Fun = [
            ("rewind", "member, year"),
            ("rewindserver", "year"),
            ("snipe", " "), ("snip", " "),
            ("dm", "member, message"),
            ("compare", "members"),
            ("msg", "member, content"),
            ("quote", " ")
        ]
        embed.add_field(
            name="Fun",
            value=format_for_embed(Fun),
            inline=False
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
