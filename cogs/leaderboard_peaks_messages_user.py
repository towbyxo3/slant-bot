import sqlite3
import discord
import os
import sqlite3
import datetime
import psutil
from discord.ext import commands
from utils import default

import sys
sys.path.append("queries")
sys.path.append("helpers")
from queries.userchatqueries import *
from queries.serverchatqueries import *
from helpers.dateformatting import *
from queries.userpeakqueries import *
from helpers.numberformatting import *


class UserpeakView(discord.ui.View):
    """
    View  that displays a leaderboard of user message peaks across
    different time periods(
    - day
    - week
    - month
    - year
    ). It provides buttons to switch between the time periods.
    """

    # PAGE NAMES
    DAILY = 1
    WEEKLY = 2
    MONTHLY = 3
    YEARLY = 4

    # representing the current page of the leaderboard
    current_page: int = 1

    async def send(self, ctx):
        """
        Send the view to a channel. It creates a message
        containing the view and updates it.
        """
        self.message = await ctx.send(view=self)
        await self.update_message()

    def create_daily_embed(self):
        """
        Creates an leaderboard of days where a member sent the most messages.
        """
        member = self.member
        ctx = self.ctx

        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        user_rank, user_date, id, user_msgs = get_user_day_peak_rank(c_cursor, member.id)

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(
            name="""
                TOP Daily User Messages Peaks
                """,
            icon_url=ctx.guild.icon)

        topten_text = ""

        for rank, (date, id, msgs) in enumerate(get_top_user_msgs_day(c_cursor), start=1):
            topten_text += f"`{rank}.`  <@{id}> **{msgs}** Msgs **{format_YMD_to_DMY(date)}**\n"

        embed.add_field(
            name="Rank | Messages | Date",
            value=topten_text, inline=False
        )
        embed.set_footer(
            icon_url=member.display_avatar,
            text=f"""
                {user_rank}. {member.name}#{member.discriminator} | {user_msgs} Msgs | {format_YMD_to_DMY(user_date)}
                    """
        )

        return embed

    def create_weekly_embed(self):
        """
        Creates an leaderboard of weeks where a member sent the most messages.
        """
        member = self.member
        ctx = self.ctx

        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        user_rank, user_date, id, user_msgs = get_user_week_peak_rank(c_cursor, member.id)
        user_year, user_weak = user_date[:4], user_date[5:]

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(
            name="""
                TOP Weekly User Messages Peaks
                """,
            icon_url=ctx.guild.icon)

        topten_text = ""

        for rank, (date, id, msgs) in enumerate(get_top_user_msgs_week(c_cursor), start=1):
            year, week = date[:4], date[5:]
            topten_text += f"`{rank}.`  <@{id}> **{abbreviate_number(msgs)}** Msgs **W{week} {year}**\n"

        embed.add_field(
            name="Rank | Messages | Week",
            value=topten_text, inline=False
        )
        embed.set_footer(
            icon_url=member.display_avatar,
            text=f"""
                {user_rank}. {member.name}#{member.discriminator} | {abbreviate_number(user_msgs)} Msgs | W{user_weak} {user_year}
                    """
        )

        return embed

    def create_monthly_embed(self):
        """
        Creates an leaderboard of months where a member sent the most messages.
        """
        member = self.member
        ctx = self.ctx

        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        user_rank, user_date, id, user_msgs = get_user_month_peak_rank(c_cursor, member.id)
        user_year, user_month = user_date[:4], get_month_name(user_date[5:])[:3]

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(
            name="""
                TOP Monthly User Messages Peaks
                """,
            icon_url=ctx.guild.icon)

        topten_text = ""

        for rank, (date, id, msgs) in enumerate(get_top_user_msgs_month(c_cursor), start=1):
            year, month = date[:4], get_month_name(date[5:])[:3]
            topten_text += f"`{rank}.`  <@{id}> **{abbreviate_number(msgs)}** Msgs **{month} {year}**\n"

        embed.add_field(
            name="Rank | Messages | Month",
            value=topten_text, inline=False
        )
        embed.set_footer(
            icon_url=member.display_avatar,
            text=f"""
                {user_rank}. {member.name}#{member.discriminator} | {abbreviate_number(user_msgs)} Msgs | {user_month} {user_year}
                    """
        )

        return embed

    def create_yearly_embed(self):
        """
        Creates an leaderboard of years where a member sent the most messages.
        """
        member = self.member
        ctx = self.ctx

        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        user_rank, user_date, id, user_msgs = get_user_year_peak_rank(c_cursor, member.id)

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(
            name="""
                TOP Yearly User Messages Peaks
                """,
            icon_url=ctx.guild.icon)

        topten_text = ""

        for rank, (date, id, msgs) in enumerate(get_top_user_msgs_year(c_cursor), start=1):
            topten_text += f"`{rank}.`  <@{id}> **{abbreviate_number(msgs)}** Msgs **{date}**\n"

        embed.add_field(
            name="Rank | Messages | Year",
            value=topten_text, inline=False
        )
        embed.set_footer(
            icon_url=member.display_avatar,
            text=f"""
                {user_rank}. {member.name}#{member.discriminator} | {abbreviate_number(user_msgs)} Msgs | {user_date}
                    """
        )

        return embed

    def create_embed(self):
        """
        Based on the current page, the respective embed is created.
        """
        if self.current_page == self.DAILY:
            return self.create_daily_embed()
        elif self.current_page == self.WEEKLY:
            return self.create_weekly_embed()
        elif self.current_page == self.MONTHLY:
            return self.create_monthly_embed()
        elif self.current_page == self.YEARLY:
            return self.create_yearly_embed()
        else:
            return None

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
        # Dictionary mapping buttons to their corresponding page values
        button_mapping = {
            self.days: self.DAILY,
            self.weeks: self.WEEKLY,
            self.months: self.MONTHLY,
            self.years: self.YEARLY
        }

        # Iterate over the dictionary items
        for button, page in button_mapping.items():
            # Reset button attributes
            button.disabled = False
            button.style = discord.ButtonStyle.green

            # Set button attributes based on the current page
            if self.current_page == page:
                button.disabled = True
                button.style = discord.ButtonStyle.gray

    @discord.ui.button(label="Days", style=discord.ButtonStyle.green)
    async def days(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 1
        await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(label="Weeks", style=discord.ButtonStyle.green)
    async def weeks(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 2
        await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(label="Months", style=discord.ButtonStyle.green)
    async def months(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 3
        await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(label="Years", style=discord.ButtonStyle.green)
    async def years(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 4
        await self.update_message()
        await interaction.response.defer()


class Userpeaks(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command(aliases=["up", "upeak", "userpeaks"])
    async def userpeak(self, ctx, member: discord.Member = None):
        """
        Displays leaderboards of days, weeks, months and years where a member
        sent most messages in that particular timeframe.
        """
        if member is None:
            member = ctx.author

        pagination_view = UserpeakView(timeout=120)
        pagination_view.ctx = ctx
        pagination_view.member = member
        await pagination_view.send(ctx)


async def setup(bot):
    await bot.add_cog(Userpeaks(bot))
