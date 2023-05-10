import discord
import psutil
from utils import default
from discord.ext import commands
import sqlite3
import sys
import os
from queries.wordqueries import *
from helpers.dateformatting import *
from helpers.numberformatting import *

sys.path.append("queries")
sys.path.append("helpers")
# from wordcloud import WordCloud, STOPWORDS
# import matplotlib.pyplot as plt


class MentionLeaderboardView(discord.ui.View):
    def __init__(self, ctx, member, bot):
        super().__init__()
        self.ctx = ctx
        self.member = member
        self.bot = bot

    @discord.ui.button(label="Tagged by", style=discord.ButtonStyle.blurple)
    async def tagged_by(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = self.member

        db = sqlite3.connect('messages.db')
        cursor = db.cursor()

        cursor.execute("""
            SELECT SUM(count)
            FROM mentions
            WHERE mention = ?
            """, (member.id,))
        total_mentions = cursor.fetchall()[0][0]

        cursor.execute("""
            SELECT *
            FROM mentions
            WHERE mention = ?
            GROUP BY author
            """, (member.id,))
        unique_authors = len(cursor.fetchall())

        cursor.execute("""
            SELECT author, count
            FROM mentions
            WHERE mention = ?
            ORDER BY count DESC
            LIMIT 10
            """, (member.id,))
        data = cursor.fetchall()
        if len(data) == 0:
            embed = discord.Embed(
                color=discord.Color.red(),
                description="Nobody has mentioned you yet")
            await interaction.message.edit(embed=embed)
            await interaction.response.defer()
            return

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_author(
            name=f"""
            {member.name}#{member.discriminator} was tagged by
            """,
            icon_url=self.ctx.guild.icon
        )

        topten_text = ""
        rank = 1

        for author, count in data:

            topten_text += f"`{rank}.`  <@{author}> **{count}** times \n"
            rank += 1

        embed.add_field(
            name="Rank | Fan | Count ",
            value=topten_text, inline=False
        )

        embed.set_footer(
            text=f"by {unique_authors} members {total_mentions} times"
        )

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()

    @discord.ui.button(label="Tagged", style=discord.ButtonStyle.blurple)
    async def tagged(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = self.member

        db = sqlite3.connect('messages.db')
        cursor = db.cursor()

        cursor.execute("""
            SELECT SUM(count)
            FROM mentions
            WHERE author = ?
            """, (member.id,))
        total_mentions = cursor.fetchall()[0][0]

        cursor.execute("""
            SELECT *
            FROM mentions
            WHERE author = ?
            GROUP BY mention
            """, (member.id,))
        unique_mentions = len(cursor.fetchall())

        cursor.execute("""
            SELECT mention, count
            FROM mentions
            WHERE AUTHOR = ?
            ORDER BY count DESC
            LIMIT 10
            """, (member.id,))
        data = cursor.fetchall()

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_author(
            name=f"""
            {member.name}#{member.discriminator} tagged
            """,
            icon_url=self.ctx.guild.icon
        )

        topten_text = ""
        rank = 1

        for mention, count in data:

            topten_text += f"`{rank}.`  <@{mention}> **{count}** times \n"
            rank += 1

        embed.add_field(
            name="Rank | Tagged | Count ",
            value=topten_text, inline=False
        )

        embed.set_footer(
            text=f"{unique_mentions} unique members {total_mentions} times "
        )

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()

    @discord.ui.button(label="Couples", style=discord.ButtonStyle.gray)
    async def couple(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = sqlite3.connect('messages.db')
        cursor = db.cursor()

        cursor.execute("""
            SELECT
              CASE WHEN t1.author < t2.author THEN t1.author ELSE t2.author END AS author1,
              CASE WHEN t1.author > t2.author THEN t1.author ELSE t2.author END AS author2,
              SUM(t1.count) AS total_mentions
            FROM mentions t1
            JOIN mentions t2 ON t1.mention = t2.author AND t1.author = t2.mention
            WHERE t1.author != t2.author
            GROUP BY
              CASE WHEN t1.author < t2.author THEN t1.author ELSE t2.author END,
              CASE WHEN t1.author > t2.author THEN t1.author ELSE t2.author END
            ORDER BY total_mentions DESC
            LIMIT 10
            """)
        data = cursor.fetchall()

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_author(
            name=f"""
            Tagged each other the most
            """,
            icon_url=self.ctx.guild.icon
        )




        topten_text = ""
        rank = 1

        for author1, author2, total_mentions in data:

            topten_text += f"`{rank}.`  <@{author1}> <@{author2}>** {int(total_mentions)}** times \n"
            rank += 1

        embed.add_field(
            name="Rank | Couple | Total Mentions",
            value=topten_text, inline=False
        )

        cursor.execute("""
            SELECT *
            FROM (
                SELECT
                  CASE WHEN t1.author < t2.author THEN t1.author ELSE t2.author END AS author1,
                  CASE WHEN t1.author > t2.author THEN t1.author ELSE t2.author END AS author2,
                  SUM(t1.count) AS total_mentions
                FROM mentions t1
                JOIN mentions t2 ON t1.mention = t2.author AND t1.author = t2.mention
                WHERE t1.author != t2.author
                GROUP BY
                  CASE WHEN t1.author < t2.author THEN t1.author ELSE t2.author END,
                  CASE WHEN t1.author > t2.author THEN t1.author ELSE t2.author END
                ORDER BY total_mentions DESC
                )
            WHERE author1 = ? OR author2 = ?            
                """, (self.member.id, self.member.id))
        data = cursor.fetchall()
        if len(data) > 0:
            auth1, auth2, total_mentions = data[0]

            author1 = await self.bot.fetch_user(int(auth1))
            author2 = await self.bot.fetch_user(int(auth2))

            embed.set_footer(
                text=f"{author1.display_name} & {author2.display_name} tagged each other {total_mentions} times "
                )

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()


    @discord.ui.button(label="Single Tags", style=discord.ButtonStyle.gray)
    async def single(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = sqlite3.connect('messages.db')
        cursor = db.cursor()

        cursor.execute("""
            SELECT *
            FROM mentions
            ORDER BY count DESC
            LIMIT 10
            """)
        data = cursor.fetchall()

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=self.ctx.guild.icon)
        embed.set_author(
            name=f"""
            Biggest Fans in {self.ctx.guild.name}
            """,
            icon_url=self.ctx.guild.icon
        )

        topten_text = ""
        rank = 1

        for author, mention, count in data:

            topten_text += f"`{rank}.`  <@{author}> @ <@{mention}> **{count}** times \n"
            rank += 1

        embed.add_field(
            name="Rank | Author | Mention | Count ",
            value=topten_text, inline=False
        )

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()


class MentionLeaderboard(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command(alises=["mentionlb", "mentionleaderboard", "mentions", "mentionslb", "taglb", "mosttags"])
    async def mention(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        db = sqlite3.connect('messages.db')
        cursor = db.cursor()

        cursor.execute("""
            SELECT *
            FROM (
              SELECT
                RANK() OVER (ORDER BY SUM(count) DESC) AS rank,
                mention,
                SUM(count) AS count
              FROM mentions
              GROUP BY mention
              ORDER BY SUM(count) DESC
            )
            WHERE mention = ?
            """, (member.id,))
        rows = cursor.fetchall()
        if len(rows) == 0:
            user_rank, user_mention, user_count = "-", id, 0
        else:
            user_rank, user_mention, user_count = rows[0]

        cursor.execute("""
            SELECT mention, SUM(count)
            FROM mentions
            GROUP BY mention
            ORDER BY sum(count) DESC
            LIMIT 10
            """)
        data = cursor.fetchall()

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_author(
            name=f"""
            Most Tagged Members
            """,
            icon_url=ctx.guild.icon
        )

        topten_text = ""
        rank = 1

        for mention, count in data:
            unique_tags = cursor.execute(
                """
                    SELECT COUNT(author)
                    FROM mentions
                    WHERE mention = ?
                """, (mention,)).fetchall()[0][0]

            topten_text += f"`{rank}.` <@{mention}> **{count}** times | {unique_tags}\n"
            rank += 1

        embed.add_field(
            name="Rank | Member | Count | Unique Taggers ",
            value=topten_text, inline=False
        )
        embed.set_footer(
            icon_url=member.avatar,
            text=f"{user_rank}. {member.name}#{member.discriminator} {user_count} times"
        )
        await ctx.send(
            embed=embed,
            view=MentionLeaderboardView(ctx, member, self.bot)
        )


async def setup(bot):
    await bot.add_cog(MentionLeaderboard(bot))
