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
# from wordcloud import WordCloud, STOPWORDS
# import matplotlib.pyplot as plt

sys.path.append("queries")
sys.path.append("helpers")


class words(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command()
    async def vocab(self, ctx):
        """
        Shows the most frequently used words in the server.
        """
        m_DB = sqlite3.connect('messages.db')
        m_cursor = m_DB.cursor()

        embed = discord.Embed(
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=ctx.guild.icon)
        server_word_count = getTotalWordCountServer(m_cursor)
        server_distinct_words = getServerDistinctWords(m_cursor)

        topten_text = "\n"
        rank = 1
        top_10_total = 0

        for word, frequency in getTopWords(m_cursor):
            topten_text += f"**{rank}**. `{word.lower()}` ~ {abbreviate_number(frequency)} \n"
            rank += 1
            top_10_total += frequency

        embed.add_field(
            name="B40s' Vocabulary",
            value=topten_text, inline=False
        )
        embed.set_footer(
            text=f"{abbreviate_number(server_word_count)} Words, "
                 f"{abbreviate_number(server_distinct_words)} Distinct",
            icon_url=ctx.guild.icon)

        await ctx.send(embed=embed)

    @commands.command()
    async def vocabuser(self, ctx, member: discord.Member = None):
        """
        Shows most frequently used words by a member.

        member: member
        """
        if member == None:
            member = ctx.author
        user = member.id

        m_DB = sqlite3.connect('messages.db')
        m_cursor = m_DB.cursor()

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=member.display_avatar)

        user_word_count = getTotalWordCountUser(m_cursor, user)
        user_distinct_words = getUserDistinctWords(m_cursor, user)

        topten_text = ""
        rank = 1
        top_10_total = 0

        for word, frequency in getTopWordsUser(m_cursor, user):
            topten_text += f"**{rank}**. `{word.lower()}` | {frequency} \n"
            rank += 1
            top_10_total += frequency

        embed.add_field(
            name=f"Vocabulary of {member.display_name}",
            value=topten_text, inline=False
        )
        embed.set_footer(
            text=f"{abbreviate_number(user_word_count)} Words, "
                 f"{abbreviate_number(user_distinct_words)} Distinct",
            icon_url=member.avatar)
        await ctx.send(embed=embed)

    @commands.command()
    async def said(self, ctx, word=None):
        if word is None:
            await ctx.send("Please add a word.\n*vocablb **word**")
            return

        member = ctx.author
        user = member.id

        m_DB = sqlite3.connect('messages.db')
        m_cursor = m_DB.cursor()

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon)
        word_count = getWordCount(m_cursor, word)

        topten_text = ""
        rank = 1
        top_10_total = 0

        author_word_count = getFrequencyWordOfUser(m_cursor, user, word)

        for user, frequency in getWordLeaderboardUser(m_cursor, word):
            topten_text += f"`{rank}.` <@{user}> | {abbreviate_number(frequency)} \n"
            rank += 1
            top_10_total += frequency
        if len(topten_text) == 0:
            await ctx.send("Nobody has used this word yet.")
            return

        topten_text += (
            f"\n**Top {rank-1} Users:**\n"
            f"{abbreviate_number(top_10_total)} ({int(top_10_total/word_count*100)}%) out of "
            f"{abbreviate_number(word_count)} {word.upper()}s"
        )

        embed.add_field(
            name=f"{word.upper()} Leaderboard",
            value=topten_text, inline=False
        )
        embed.set_footer(
            text=f"{member.display_name} | {abbreviate_number(author_word_count)}", icon_url=member.avatar)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(words(bot))
