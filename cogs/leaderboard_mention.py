import discord
import psutil
from utils import default
from discord.ext import commands
import sqlite3
import sys
import os
from helpers.numberformatting import abbreviate_number

sys.path.append("queries")
sys.path.append("helpers")
# from wordcloud import WordCloud, STOPWORDS
# import matplotlib.pyplot as plt


class MentionLeaderboardView(discord.ui.View):
    """
    View that displays a 3 different leaderboard which you can switch between.
    A custom Discord UI view that displays three different leaderboards, allowing users to switch between them.
    Page 1: Members with the highest number of mentions.
    Page 2: Members who have mentioned a specific member the most.
    Page 3: Members who have been mentioned the most by the specific member.
    """

    # PAGE NAMES
    MENTIONS_LB = 1
    TAGGED_BY = 2
    TAGGED = 3

    # representing the current page of the leaderboard
    # page 1 for registration date
    # page 2 for join date
    current_page: int = 1

    async def send(self, ctx):
        """
        Send the view to a channel. It creates a message
        containing the view and updates it.
        """
        self.message = await ctx.send(view=self)
        await self.update_message()

    def create_mention_lb_embed(self):
        """
        Creates an embed for the most mentioned members in the server.
        """
        member = self.member
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
        embed.set_thumbnail(url=self.ctx.guild.icon)
        embed.set_author(
            name=f"""
            Most Tagged Members
            """,
            icon_url=self.ctx.guild.icon
        )

        topten_text = ""

        for rank, (mention, count) in enumerate(data, start=1):
            unique_tags = cursor.execute(
                """
                    SELECT COUNT(author)
                    FROM mentions
                    WHERE mention = ?
                """, (mention,)).fetchall()[0][0]

            topten_text += f"`{rank}.` <@{mention}> **{abbreviate_number(count)}** times | {unique_tags}\n"

        embed.add_field(
            name="Rank | Member | Count | Unique Taggers ",
            value=topten_text, inline=False
        )
        embed.set_footer(
            icon_url=member.avatar,
            text=f"{user_rank}. {member.name}#{member.discriminator} {abbreviate_number(user_count)} times"
        )

        return embed

    def create_tagged_by_embed(self):
        """
        Creates an embed for members who tagged the specific member the most.
        """
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
                description="Nobody has mentioned you yet"
            )
            return embed

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=self.ctx.guild.icon)
        embed.set_author(
            name=f"""
            {member.name}#{member.discriminator} was tagged by
            """,
            icon_url=member.display_avatar
        )

        topten_text = ""

        for rank, (author, count) in enumerate(data, start=1):
            topten_text += f"`{rank}.`  <@{author}> **{abbreviate_number(count)}** times \n"

        embed.add_field(
            name="Rank | Fan | Count ",
            value=topten_text, inline=False
        )

        embed.set_footer(
            text=f"by {unique_authors} members {abbreviate_number(total_mentions)} times"
        )

        return embed

    def create_tagged_embed(self):
        """
        Creates an embed for members who were tagged the most by the specific member.
        """
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
        embed.set_thumbnail(url=self.ctx.guild.icon)
        embed.set_author(
            name=f"""
            {member.name}#{member.discriminator} tagged
            """,
            icon_url=member.display_avatar
        )

        topten_text = ""

        for rank, (mention, count) in enumerate(data, start=1):
            topten_text += f"`{rank}.`  <@{mention}> **{abbreviate_number(count)}** times \n"

        embed.add_field(
            name="Rank | Tagged | Count ",
            value=topten_text, inline=False
        )

        embed.set_footer(
            text=f"{unique_mentions} unique members {abbreviate_number(total_mentions)} times "
        )

        return embed

    def create_embed(self):
        """
        Based on the current page, the respective embed is created.
        """
        if self.current_page == self.MENTIONS_LB:
            return self.create_mention_lb_embed()
        if self.current_page == self.TAGGED_BY:
            return self.create_tagged_by_embed()
        if self.current_page == self.TAGGED:
            return self.create_tagged_embed()

    async def update_message(self):
        """
        Updates the message with the current state of the view.
        It updates the buttons and the embed.
        """
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(), view=self)

    def update_buttons(self):
        """
        Updates the state of the buttons based on the current page.
        """
        self.mentionslb.disabled = False
        self.tagged_by.disabled = False
        self.tagged.disabled = False
        self.mentionslb.style = discord.ButtonStyle.green
        self.tagged_by.style = discord.ButtonStyle.green
        self.tagged.style = discord.ButtonStyle.green

        if self.current_page == self.MENTIONS_LB:
            self.mentionslb.disabled = True
            self.mentionslb.style = discord.ButtonStyle.gray

        if self.current_page == self.TAGGED_BY:
            self.tagged_by.disabled = True
            self.tagged_by.style = discord.ButtonStyle.gray

        if self.current_page == self.TAGGED:
            self.tagged.disabled = True
            self.tagged.style = discord.ButtonStyle.gray

    @discord.ui.button(label="Mention Leaderboard", style=discord.ButtonStyle.gray)
    async def mentionslb(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.MENTIONS_LB
        await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(label="Tagged by", style=discord.ButtonStyle.blurple)
    async def tagged_by(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.TAGGED_BY
        await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(label="Tagged", style=discord.ButtonStyle.blurple)
    async def tagged(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.TAGGED
        await self.update_message()
        await interaction.response.defer()


class MentionLeaderboard(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command(alises=["mentionlb", "mentionleaderboard", "mentions", "mentionslb", "taglb", "mosttags"])
    async def mention(self, ctx, member: discord.Member = None):
        """
        Displays three mention leaderboards and allows switching between them,
        - showing the top members with the most mentions,
        - the members who mention a specific member the most,
        - and the members who are mentioned the most by a specific member.
        """
        if member is None:
            member = ctx.author

        pagination_view = MentionLeaderboardView(timeout=120)
        pagination_view.ctx = ctx
        pagination_view.member = member
        await pagination_view.send(ctx)


async def setup(bot):
    await bot.add_cog(MentionLeaderboard(bot))
