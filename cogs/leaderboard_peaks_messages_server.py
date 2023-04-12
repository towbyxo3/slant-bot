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

    @discord.ui.button(label="Day", style=discord.ButtonStyle.blurple)
    async def Day(self, interaction: discord.Interaction, button: discord.ui.Button):
        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        days = dayEntries(c_cursor)

        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=self.ctx.message.created_at)
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_author(
            name=f"""
                Daily Messages Peak
                """,
            icon_url=self.ctx.guild.icon
        )

        topten_text = ""
        rank = 1

        for date, msgs in dayMessagesPeak(c_cursor):
            unique_chatters_day = distinctChattersDay(c_cursor, date)
            date = DbYYYformat(date)
            topten_text += f"`{rank}.` **{abbreviate_number(msgs)}** Msgs by **{unique_chatters_day}** Members | {date} \n"
            rank += 1

        embed.add_field(
            name="Rank | Messages | Date",
            value=topten_text
        )
        embed.set_footer(text=f"{rank-1} out of {days} Days")

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()

    @discord.ui.button(label="Week", style=discord.ButtonStyle.blurple)
    async def Week(self, interaction: discord.Interaction, button: discord.ui.Button):
        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=self.ctx.message.created_at)
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_author(
            name=f"""
                Weekly Messages Peak
                """,
            icon_url=self.ctx.guild.icon)

        topten_text = ""
        rank = 1

        for date, msgs in weekMessagesPeak(c_cursor):
            year, week = date.split('-')
            unique_chatters_week = distinctChattersWeek(c_cursor, year, week)
            topten_text += f"`{rank}.` **{abbreviate_number(msgs)}** Msgs by **{unique_chatters_week}** Members | W{week} {year}\n"
            rank += 1

        weeks = weekEntries(c_cursor)
        embed.add_field(
            name="Rank | Messages | Week",
            value=topten_text)
        embed.set_footer(text=f"{rank-1} out of {weeks} Weeks")

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()

    @discord.ui.button(label="Month", style=discord.ButtonStyle.blurple)
    async def Month(self, interaction: discord.Interaction, button: discord.ui.Button):
        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=self.ctx.message.created_at)
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_author(
            name=f"""
                Monthly Messages Peak
                """,
            icon_url=self.ctx.guild.icon)

        topten_text = ""
        rank = 1

        for date, msgs in monthMessagesPeak(c_cursor):
            year, month = date.split('-')
            unique_chatters_month = distinctChattersMonth(c_cursor, year, month)
            month = get_month_name(month)[:3]
            topten_text += f"`{rank}.` **{abbreviate_number(msgs)}** Msgs by **{unique_chatters_month}** Members | {month} {year}\n"
            rank += 1

        months = monthEntries(c_cursor)
        embed.add_field(
            name="Rank | Messages | Month",
            value=topten_text)
        embed.set_footer(text=f"{rank-1} out of {months} Months")

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()

    @discord.ui.button(label="Year", style=discord.ButtonStyle.blurple)
    async def Year(self, interaction: discord.Interaction, button: discord.ui.Button):
        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=self.ctx.message.created_at)
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_author(
            name=f"""
                Yearly Messages Peak
                """,
            icon_url=self.ctx.guild.icon)

        topten_text = ""
        rank = 1

        for date, msgs in yearMessagesPeak(c_cursor):
            unique_chatters_year = distinctChattersYear(c_cursor, date)
            topten_text += f"`{rank}.` **{abbreviate_number(msgs)}** Msgs by **{unique_chatters_year}** Members | {date}\n"
            rank += 1

        years = yearEntries(c_cursor)
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

    @commands.command()
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
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_footer(
            text=f"Server ID: {ctx.guild.id}"
        )
        await ctx.send(embed=embed, view=Serverpeak(ctx))


async def setup(bot):
    await bot.add_cog(serverstats(bot))
