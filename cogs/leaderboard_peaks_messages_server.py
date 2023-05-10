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


class Serverpeak(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    @discord.ui.button(label="Days", style=discord.ButtonStyle.blurple)
    async def days(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        rank = 1

        for date, msgs in get_top_server_msgs_day(c_cursor):
            unique_chatters_day = get_distinct_chatters_count_day(c_cursor, date)
            date = format_YMD_to_DMY(date)
            topten_text += f"`{rank}.` **{abbreviate_number(msgs)}** Msgs by **{unique_chatters_day}** Members | {date} \n"
            rank += 1

        embed.add_field(
            name="Rank | Messages | Date",
            value=topten_text
        )
        embed.set_footer(text=f"{rank-1} out of {days} Days")

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()

    @discord.ui.button(label="Weeks", style=discord.ButtonStyle.blurple)
    async def weeks(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        rank = 1

        for date, msgs in get_top_server_msgs_week(c_cursor):
            year, week = date.split('-')
            unique_chatters_week = get_distinct_chatters_count_week(c_cursor, year, week)
            topten_text += f"`{rank}.` **{abbreviate_number(msgs)}** Msgs by **{unique_chatters_week}** Members | W{week} {year}\n"
            rank += 1

        weeks = get_week_chat_entries_count(c_cursor)
        embed.add_field(
            name="Rank | Messages | Week",
            value=topten_text)
        embed.set_footer(text=f"{rank-1} out of {weeks} Weeks")

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()

    @discord.ui.button(label="Months", style=discord.ButtonStyle.blurple)
    async def months(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        rank = 1

        for date, msgs in get_top_server_msgs_month(c_cursor):
            year, month = date.split('-')
            unique_chatters_month = get_distinct_chatters_count_month(c_cursor, year, month)
            month = get_month_name(month)[:3]
            topten_text += f"`{rank}.` **{abbreviate_number(msgs)}** Msgs by **{unique_chatters_month}** Members | {month} {year}\n"
            rank += 1

        months = get_month_chat_entries_count(c_cursor)
        embed.add_field(
            name="Rank | Messages | Month",
            value=topten_text)
        embed.set_footer(text=f"{rank-1} out of {months} Months")

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()

    @discord.ui.button(label="Years", style=discord.ButtonStyle.blurple)
    async def years(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        rank = 1

        for date, msgs in get_top_server_msgs_year(c_cursor):
            unique_chatters_year = get_distinct_chatters_count_year(c_cursor, date)
            topten_text += f"`{rank}.` **{abbreviate_number(msgs)}** Msgs by **{unique_chatters_year}** Members | {date}\n"
            rank += 1

        years = get_year_chat_entries_count(c_cursor)
        embed.add_field(
            name="Rank | Messages | Year",
            value=topten_text)
        embed.set_footer(text=f"{rank-1} out of {years} Years")

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()


class serverstats(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command(aliases=["serverpeaks"])
    async def serverpeak(self, ctx):
        """
        Most Messages within a timeframe
        """
        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at,
            title=f"{ctx.guild.name} Server Chat Peaks",
            description=":information_source: `Peak Messages in a Day, Week, Month or Year`"
        )
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_footer(
            text=f"Server ID: {ctx.guild.id}"
        )
        await ctx.send(embed=embed, view=Serverpeak(ctx))


async def setup(bot):
    await bot.add_cog(serverstats(bot))
