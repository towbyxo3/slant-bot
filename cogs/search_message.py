import sqlite3
import discord
from discord.ext import commands
from utils import default
from typing import Optional
import sys
from helpers.dateformatting import format_YMD_to_DMY
import requests

sys.path.append("helpers")


def get_quote():
    response = requests.get("https://api.quotable.io/random")
    data = response.json()
    return data["content"], data["author"]


class Quote(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()

    @commands.command(aliases=['msg'])
    async def quote(self, ctx, member: Optional[discord.Member] = None, *, word: Optional[str] = None):
        """
        Displays a random message
        by a member
        by a member containing a string
        containing a string

        member: a random message by a certain member (containing a certain substring)
        word: a substring that the displayed message should contain
        """
        if word is None:
            word = "test"

        db = sqlite3.connect('chat.db')
        cursor = db.cursor()

        if word is not None and member is not None:
            word = '%' + word + '%'
            cursor.execute("""
                SELECT authorid, date, content
                FROM B40
                WHERE authorid = ? AND LENGTH(content) > 10 AND content LIKE ?
                ORDER BY RANDOM()
                LIMIT 1
                """, (str(member.id), word))
        elif word is None and member is None:
            cursor.execute("""
                SELECT authorid,date, content
                FROM B40
                WHERE LENGTH(content)
                ORDER BY RANDOM()
                LIMIT 1
                """)
        elif member is not None and word is None:
            cursor.execute("""
                SELECT authorid, date, content
                FROM B40
                WHERE authorid = ? AND LENGTH(content) > 10
                ORDER BY RANDOM()
                LIMIT 1
                """, (str(member.id),))
        elif member is None and word is not None:
            word = '%' + word + '%'
            cursor.execute("""
                SELECT authorid, date, content
                FROM B40
                WHERE LENGTH(content) > 10 AND content LIKE ?
                ORDER BY RANDOM()
                LIMIT 1
                """, (word,))

        data = cursor.fetchone()

        if data is None:
            embed = discord.Embed(
                description=f"No Message found",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        id, date, content = data
        try:
            member = await self.bot.fetch_user(id)
        except:
            name = "Deleted User"
            av = None
        name = f"{member.name}#{member.discriminator}"
        av = member.avatar

        embed = discord.Embed(
            description=content,
            color=discord.Color.green()
        )
        embed.set_author(
            icon_url=av,
            name=f"{name} | {format_YMD_to_DMY(date[:10])}"
        )
        await ctx.send(embed=embed)


"""    @commands.command()
    async def quote(self, ctx):
        # Get a random quote from the API
        quote, author = get_quote()

        embed = discord.Embed(
            description=f"{quote}\n*-{author}*",
            color=discord.Color.green()
        )

        # Send the quote to the channel
        await ctx.send(embed=embed)
"""


async def setup(bot):
    await bot.add_cog(Quote(bot))
