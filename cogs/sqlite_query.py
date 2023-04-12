import sqlite3
import discord
from discord.ext import commands
from utils import default
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import numpy as np
from typing import Optional
import sys
sys.path.append("helpers")
from helpers.numberformatting import *
from helpers.dateformatting import DbYYYformat



class sqlqueries(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()

    @commands.command()
    async def sql(self, ctx, db, *, str):
        if ctx.author.id != 95563800354238464:
            await ctx.send("Not the owner")
            return
        db = sqlite3.connect(db)
        cursor = db.cursor()
        cursor.execute(str)
        data = cursor.fetchall()
        print(data)
        await ctx.send(data)



async def setup(bot):
    await bot.add_cog(sqlqueries(bot))
