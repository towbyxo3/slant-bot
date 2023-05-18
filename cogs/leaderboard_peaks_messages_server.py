import sqlite3
import discord
import psutil
import os
import sqlite3
import datetime
from discord.ext import commands
from utils import default

import sys
sys.path.append("queries")
sys.path.append("helpers")
from queries.userchatqueries import *
from queries.serverchatqueries import *
from helpers.dateformatting import *
from queries.serverpeakqueries import *
from helpers.numberformatting import *


class ServerpeakView(discord.ui.View):
    """
    View  that displays a leaderboard of server message activity across
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

    # representing the current page of the pagination
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
        Creates an leaderboard of days where most server messages were sent.
        """
        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        days = get_day_chat_entries_count(c_cursor)

        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=self.ctx.message.created_at)
        embed.set_thumbnail(url=self.ctx.guild.icon)
        embed.set_author(
            name="""
                Daily Messages Peak
                """,
            icon_url=self.ctx.guild.icon
        )

        topten_text = ""

        for rank, (date, msgs) in enumerate(get_top_server_msgs_day(c_cursor), start=1):
            unique_chatters_day = get_distinct_chatters_count_day(c_cursor, date)
            date = format_YMD_to_DMY(date)
            topten_text += f"`{rank}.` **{abbreviate_number(msgs)}** Msgs by **{unique_chatters_day}** Members | {date} \n"

        embed.add_field(
            name="Rank | Messages | Date",
            value=topten_text
        )
        embed.set_footer(text=f"{rank} out of {days} Days")

        return embed

    def create_weekly_embed(self):
        """
        Creates an leaderboard of weeks where most server messages were sent.
        """
        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=self.ctx.message.created_at)
        embed.set_thumbnail(url=self.ctx.guild.icon)
        embed.set_author(
            name=f"""
                Weekly Messages Peak
                """,
            icon_url=self.ctx.guild.icon)

        topten_text = ""

        for rank, (date, msgs) in enumerate(get_top_server_msgs_week(c_cursor), start=1):
            year, week = date.split('-')
            unique_chatters_week = get_distinct_chatters_count_week(c_cursor, year, week)
            topten_text += f"`{rank}.` **{abbreviate_number(msgs)}** Msgs by **{unique_chatters_week}** Members | W{week} {year}\n"

        weeks = get_week_chat_entries_count(c_cursor)
        embed.add_field(
            name="Rank | Messages | Week",
            value=topten_text)
        embed.set_footer(text=f"{rank} out of {weeks} Weeks")

        return embed

    def create_monthly_embed(self):
        """
        Creates an leaderboard of months where most server messages were sent.
        """
        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=self.ctx.message.created_at)
        embed.set_thumbnail(url=self.ctx.guild.icon)
        embed.set_author(
            name=f"""
                Monthly Messages Peak
                """,
            icon_url=self.ctx.guild.icon)

        topten_text = ""

        for rank, (date, msgs) in enumerate(get_top_server_msgs_month(c_cursor), start=1):
            year, month = date.split('-')
            unique_chatters_month = get_distinct_chatters_count_month(c_cursor, year, month)
            month = get_month_name(month)[:3]
            topten_text += f"`{rank}.` **{abbreviate_number(msgs)}** Msgs by **{unique_chatters_month}** Members | {month} {year}\n"

        months = get_month_chat_entries_count(c_cursor)
        embed.add_field(
            name="Rank | Messages | Month",
            value=topten_text)
        embed.set_footer(text=f"{rank} out of {months} Months")

        return embed

    def create_yearly_embed(self):
        """
        Creates an leaderboard of years where most server messages were sent.
        """
        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=self.ctx.message.created_at)
        embed.set_thumbnail(url=self.ctx.guild.icon)
        embed.set_author(
            name=f"""
                Yearly Messages Peak
                """,
            icon_url=self.ctx.guild.icon)

        topten_text = ""

        for rank, (date, msgs) in enumerate(get_top_server_msgs_year(c_cursor), start=1):
            unique_chatters_year = get_distinct_chatters_count_year(c_cursor, date)
            topten_text += f"`{rank}.` **{abbreviate_number(msgs)}** Msgs by **{unique_chatters_year}** Members | {date}\n"

        years = get_year_chat_entries_count(c_cursor)
        embed.add_field(
            name="Rank | Messages | Year",
            value=topten_text)
        embed.set_footer(text=f"{rank} out of {years} Years")

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
        self.days.disabled = False
        self.weeks.disabled = False
        self.months.disabled = False
        self.years.disabled = False
        self.days.style = discord.ButtonStyle.green
        self.weeks.style = discord.ButtonStyle.green
        self.months.style = discord.ButtonStyle.green
        self.years.style = discord.ButtonStyle.green

        if self.current_page == self.DAILY:
            self.days.disabled = True
            self.days.style = discord.ButtonStyle.gray

        if self.current_page == self.WEEKLY:
            self.weeks.disabled = True
            self.weeks.style = discord.ButtonStyle.gray

        if self.current_page == self.MONTHLY:
            self.months.disabled = True
            self.months.style = discord.ButtonStyle.gray

        if self.current_page == self.YEARLY:
            self.years.disabled = True
            self.years.style = discord.ButtonStyle.gray

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


class Serverpeak(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command(aliases=["serverpeaks", "sp", "speak"])
    async def serverpeak(self, ctx):
        """
        Displays leaderboards of days, weeks, months and years where most
        messages were sent in the server.
        """
        pagination_view = ServerpeakView(timeout=120)
        pagination_view.ctx = ctx
        await pagination_view.send(ctx)


async def setup(bot):
    await bot.add_cog(Serverpeak(bot))
