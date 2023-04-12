import sqlite3
import discord
from discord.ext import commands
from utils import default
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import sys
import random



class Grunge(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id in [432651461021663252, 883369368690511962, 121339500482920448]:
            random_num = random.randint(0, 25) # Generate a random integer between 0 and 1 (inclusive)
            if random_num == 0:
                await message.add_reaction('💀')

    @commands.command()
    async def vcnuke(self, ctx):
        if ctx.author.id != 95563800354238464:
            return
        for channel in ctx.guild.voice_channels:
            try:
                await channel.delete()
            except:
                continue

    @commands.command()
    async def vcunnuke(self, ctx):
        if ctx.author.id != 95563800354238464:
            return
        # Define the prefixes and suffixes for the voice channels
        prefixes = ["1", "2", "3", "5"]
        suffixes = ["a", "b", "c"]

        # Find the category where the new channels will be created
        category_name = "VC"
        category_vc = discord.utils.get(ctx.guild.categories, name=category_name)

        if category_vc is None:
            await ctx.send(f"No category found with name {category_name}")
            return

        # Calculate the position of the first channel to create
        position = len(category_vc.voice_channels)

        # Loop through each prefix and suffix to create the voice channels
        for prefix in prefixes:
            for suffix in suffixes:
                if prefix not in ["2", "3"] and suffix == "c":
                    break
                channel_name = f"{prefix}{suffix}"
                user_limit = prefix
                await ctx.guild.create_voice_channel(channel_name, category=category_vc, position=position, user_limit=user_limit)
                position += 1

        category_name = "SCRIM"
        category_vc = discord.utils.get(ctx.guild.categories, name=category_name)

        if category_vc is None:
            await ctx.send(f"No category found with name {category_name}")
            return

        # Create the voice channels
        user_limit = 5
        await ctx.guild.create_voice_channel("A", category=category_vc, user_limit=user_limit)
        await ctx.guild.create_voice_channel("B", category=category_vc, user_limit=user_limit)



async def setup(bot):
    await bot.add_cog(Grunge(bot))
