import sqlite3
import discord
import os
# import datetime
import psutil
from discord.ext import commands
import sys
from utils import default
from queries.serverchatqueries import get_day_chat_entries_count
from queries.crownqueries import get_user_crown_rank, top_10_crowns


sys.path.append("queries")
sys.path.append("helpers")


class Crowns(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command(aliases=["crown", "crownlb", "crownleaderboard"])
    async def crowns(self, ctx, member: discord.Member = None):
        """
        Shows leaderboard of members who got the most crowns. A crown is
        earned for being the member with the most messages sent in a day.
        """
        if member is None:
            member = ctx.author
        user = member.id

        # Connect to database
        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        # Get crown stats
        possible_crowns = get_day_chat_entries_count(c_cursor)
        user_id, user_crowns, user_rank = get_user_crown_rank(c_cursor, user)

        # Construct embed
        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(
            name="""
                Crown 👑 Leaderboard\n👑: Most Msgs in a Day
                """,
            icon_url=ctx.guild.icon
        )

        topten_text = ""
        leaderboard_total_crowns = 0

        for rank, (id, crowns) in enumerate(top_10_crowns(c_cursor), start=1):
            topten_text += f"`{rank}.`  <@{id}> **{crowns}** 👑\n"
            leaderboard_total_crowns += crowns

        top_10_contribution = int(leaderboard_total_crowns / possible_crowns * 100)
        info_text = (
            f"\n**Top {rank}** has **{leaderboard_total_crowns}** "
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
    await bot.add_cog(Crowns(bot))
