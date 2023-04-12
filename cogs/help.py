import sqlite3
import discord
import psutil
import os
from discord import ui
import sqlite3
import datetime
from typing import Union

from discord.ext import commands
from utils import default
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import io
import aiohttp


def embedFormat(tuple):
    return '\n'.join([f"`{command}`" + " " + argument for command, argument in tuple])


class help(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title="B40 Commands", color=discord.Color.blue())


        # moderation = ["ban", "kick", "find", "massban", "mute", "nickname", "prune", "unban", "unmute"]
        # embed.add_field(
        #     name="Moderation",
        #     value=embedFormat(moderation),
        #     inline= False
        #     )

        Info = [("avatar", "member"), ("avatarhistory", "member"), ("userinfo", "member"), ("serverinfo", " "), ("avatar", "member"), ("about", " "), ("names", "member"), ("invite", " "), ("country", "country"), ("covid", "country"), ("ping", " "), ("roles", " "), ("recent", " ")]
        embed.add_field(
            name="Info",
            value=embedFormat(Info),
            inline= False
            )
        Leaderboards = [("leaderboard", "member"), ("userpeak", "member"), ("serverpeak", "member"), ("age", " "), ("crowns", "member"), ("mention", "member")]
        embed.add_field(
            name="Leaderboard",
            value=embedFormat(Leaderboards)
            )
        Vocabulary = [("vocab", " "), ("vocabuser", "member"), ("said", "member"), ("wordcloud", "member"), ("wordcloudserver", "min word length")]
        embed.add_field(
            name="Vocabulary",
            value=embedFormat(Vocabulary),
            inline= False
            )

        VC = [("massmove", "channel"), ("massmoveall", "channel")]
        embed.add_field(
            name="VC",
            value=embedFormat(VC),
            inline= False
            )

        Fun = [("rewind", "member, year"), ("rewindserver", "year"), ("snipe", " "), ("snip", " "), ("dm", "member, message"), ("compare", "members"), ("msg", "member, content"), ("quote", " ")]
        embed.add_field(
            name="Fun",
            value=embedFormat(Fun),
            inline= False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(help(bot))
