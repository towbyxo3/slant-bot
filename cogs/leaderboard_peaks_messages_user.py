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
from queries.peakqueries import *
from helpers.numberformatting import *


class Userpeak(discord.ui.View):
    def __init__(self, ctx, member): 
        super().__init__()
        self.ctx = ctx
        self.member = member


    @discord.ui.button(label="Day", style=discord.ButtonStyle.blurple)
    async def Day(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.member.id

        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        user_rank, user_date, id, user_msgs = TopChatUserPeaksRank(c_cursor, user)

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_author(
            name=f"""
                TOP Daily User Messages
                """,
            icon_url=self.ctx.guild.icon)


        topten_text = ""
        rank = 1

        for date, id, msgs in TopChatUserPeaks(c_cursor):
            topten_text += f"`{rank}.`  <@{id}> **{msgs}** Msgs **{DbYYYformat(date)}**\n"
            rank+=1

        embed.add_field(
            name="Rank | Messages | Date",
            value=topten_text, inline=False
                        )
        embed.set_footer(
            icon_url=self.member.avatar,
            text=f"""
                {user_rank}. {self.member.name}#{self.member.discriminator} | {user_msgs} Msgs | {DbYYYformat(user_date)} 
                    """) 

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()


    @discord.ui.button(label="Weekly", style=discord.ButtonStyle.blurple)
    async def Weekly(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.member.id

        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        user_rank, user_date, id, user_msgs = TopChatUserPeaksWeekRank(c_cursor, user)
        user_year, user_weak= user_date[:4], user_date[5:]

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_author(
            name=f"""
                TOP Weekly User Messages
                """,
            icon_url=self.ctx.guild.icon)


        topten_text = ""
        rank = 1

        for date, id, msgs in TopChatUserPeaksWeek(c_cursor):
            year, week = date[:4], date[5:]
            topten_text += f"`{rank}.`  <@{id}> **{abbreviate_number(msgs)}** Msgs **W{week} {year}**\n"
            rank+=1

        embed.add_field(
            name="Rank | Messages | Week",
            value=topten_text, inline=False
                        )
        embed.set_footer(
            icon_url=self.member.avatar,
            text=f"""
                {user_rank}. {self.member.name}#{self.member.discriminator} | {abbreviate_number(user_msgs)} Msgs | W{user_weak} {user_year} 
                    """) 

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()


    @discord.ui.button(label="Monthly", style=discord.ButtonStyle.blurple)
    async def Monthly(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.member.id

        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        user_rank, user_date, id, user_msgs = TopChatUserPeaksMonthRank(c_cursor, user)
        user_year, user_month= user_date[:4], get_month_name(user_date[5:])[:3]

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_author(
            name=f"""
                TOP Monthly User Messages
                """,
            icon_url=self.ctx.guild.icon)


        topten_text = ""
        rank = 1

        for date, id, msgs in TopChatUserPeaksMonth(c_cursor):
            year, month = date[:4], get_month_name(date[5:])[:3]
            topten_text += f"`{rank}.`  <@{id}> **{abbreviate_number(msgs)}** Msgs **{month} {year}**\n"
            rank+=1

        embed.add_field(
            name="Rank | Messages | Month",
            value=topten_text, inline=False
                        )
        embed.set_footer(
            icon_url=self.member.avatar,
            text=f"""
                {user_rank}. {self.member.name}#{self.member.discriminator} | {abbreviate_number(user_msgs)} Msgs | {user_month} {user_year} 
                    """)

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()


    @discord.ui.button(label="Yearly", style=discord.ButtonStyle.blurple)
    async def Yearly(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = self.member.id

        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        user_rank, user_date, id, user_msgs = TopChatUserPeaksYearRank(c_cursor, user)

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_author(
            name=f"""
                TOP Yearly User Messages
                """,
            icon_url=self.ctx.guild.icon)


        topten_text = ""
        rank = 1

        for date, id, msgs in TopChatUserPeaksYear(c_cursor):
            topten_text += f"`{rank}.`  <@{id}> **{abbreviate_number(msgs)}** Msgs **{date}**\n"
            rank+=1

        embed.add_field(
            name="Rank | Messages | Year",
            value=topten_text, inline=False
                        )
        embed.set_footer(
            icon_url=self.member.avatar,
            text=f"""
                {user_rank}. {self.member.name}#{self.member.discriminator} | {abbreviate_number(user_msgs)} Msgs | {user_date} 
                    """) 

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()






class peaks(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())


    @commands.command()
    async def userpeak(self, ctx, member: discord.Member = None):
        """
        Most messages sent within timeframe
        """
        if member == None:
            member = ctx.author
        user = member.id

        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at,
            title="User Chat Peaks",
            description=":information_source: `Peak Messages in a Day, Week, Month or Year`"
            )
        embed.set_thumbnail(url="https://i.imgur.com/7dyGz0S.jpg")
        embed.set_footer(
            text=f"Server ID: {ctx.guild.id}"
            )   

        await ctx.send(embed=embed, view=Userpeak(ctx, member))




async def setup(bot):
    await bot.add_cog(peaks(bot))