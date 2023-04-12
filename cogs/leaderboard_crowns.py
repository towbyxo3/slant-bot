import sqlite3
import discord
import os
# import datetime
import psutil
from discord.ext import commands
from utils import default
import sys
sys.path.append("queries")
sys.path.append("helpers")
from queries.userchatqueries import *
from queries.serverchatqueries import *
from helpers.dateformatting import *
from queries.peakqueries import *
from queries.crownqueries import *


class crowns(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command()
    async def crowns(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        user = member.id

        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        possible_crowns = dayEntries(c_cursor)
        user_id, user_crowns, user_rank = dayCrownsRank(c_cursor, user)

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(
            name=f"""
                Crown 👑 Leaderboard\n👑: Most Msgs in a Day
                """,
            icon_url=ctx.guild.icon)

        topten_text = ""
        rank = 1
        leaderboard_total_crowns = 0

        for id, crowns in dayCrowns(c_cursor):

            topten_text += f"`{rank}.`  <@{id}> **{crowns}** 👑\n"
            rank += 1
            leaderboard_total_crowns += crowns

        top_10_contribution = int(leaderboard_total_crowns / possible_crowns * 100)
        info_text = (
            f"\n**Top {rank-1}** has **{leaderboard_total_crowns}** "
            f"({top_10_contribution}%) out of **{possible_crowns}** 👑"
        )
        topten_text += info_text
        embed.add_field(
            name="Rank | User | Crowns ",
            value=topten_text, inline=False
        )
        embed.set_footer(
            icon_url=member.avatar,
            text=f"{user_rank}. {member.name}#{member.discriminator} | {user_crowns} 👑"
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(crowns(bot))
