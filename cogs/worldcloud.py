import sqlite3
import discord
from discord.ext import commands
from utils import default
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import sys
from helpers.dateformatting import *
from helpers.numberformatting import abbreviate_number

sys.path.append("helpers")
sys.path.append("queries")


def get_vocab_user(cursor, word):
    cursor.execute("""
            SELECT id, COUNT(id)
            FROM words
            WHERE word = ?
            GROUP BY id
            ORDER BY COUNT(id) DESC
            LIMIT 10
            """, (word.upper(), ))
    rows = cursor.fetchall()
    return rows


def get_word_frequency_server(cursor, word):
    cursor.execute("""
            SELECT COUNT(id)
            FROM words
            WHERE word = ?
            """, (word.upper(), ))
    count = cursor.fetchall()[0][0]
    return count


def get_word_frequency_user(cursor, id, word):
    cursor.execute("""
        SELECT COUNT(word)
        FROM words
        WHERE id = ? AND word = ?
        """, (id, word.upper()))
    count = cursor.fetchall()[0][0]
    return count


def get_most_frequent_words(m_cursor, length):
    """
    Returns a list of tuples ordered by frequency of word

    m_cursor: db.cursor()
    length: minimum length of the word
    """
    m_cursor.execute("""
        SELECT word, count(word)
        FROM words
        WHERE LENGTH(word) > ?
        GROUP BY word
        ORDER BY count(word) DESC
        LIMIT 150
        """, (length,))
    data = m_cursor.fetchall()
    # filters channels, mentions, emotes
    filtered_data = [(word, count) for word, count in data if not (word.startswith('@') or word.startswith(':') or word.startswith('<') or word.startswith('#') or "'" in word)]

    return filtered_data


def get_word_count_length(m_cursor, length):
    """
    Returns the count of words that are longer than given length.

    length: minimum length of the word
    """
    m_cursor.execute("""
    SELECT COUNT(*)
    FROM words
    WHERE LENGTH(word) > ?
    """, (length,))
    count = m_cursor.fetchone()[0]

    return count


def get_most_frequent_words_user(m_cursor, id):
    """
    Returns a list of tuples ordered by frequency of word
    by member

    cursor: db.cursor()
    id: member id
    """
    m_cursor.execute("""
        SELECT word, COUNT(word)
        FROM words WHERE LENGTH(word) > 3 AND ID = ?
        GROUP BY word
        ORDER BY count(word) DESC
        LIMIT 150
        """, (id,))
    data = m_cursor.fetchall()
    filtered_data = [(word, count) for word, count in data if not (word.startswith('@') or word.startswith(':') or word.startswith('<') or word.startswith('#') or "'" in word)]

    return filtered_data


def get_sample_size(m_cursor):
    """
    Returns sample size

    m_cursor: db.cursor()
    """
    m_cursor.execute("""
        SELECT max(RowId)
        FROM words
        """)
    count = m_cursor.fetchone()[0]

    return count


def get_unique_words_count(m_cursor):
    """
    Returns distinct words count

    m_cursor: db.cursor()
    """
    m_cursor.execute("""
        SELECT COUNT(DISTINCT word)
        FROM words
        """)
    count = m_cursor.fetchone()[0]
    return count


def get_sample_size_user(m_cursor, id):
    """
    Returns sample size count of user

    m_cursor: db.cursor()
    id: member id
    """
    m_cursor.execute("""
        SELECT COUNT(word)
        FROM words
        WHERE id = ?
        """, (id,))
    count = m_cursor.fetchone()[0]

    return count


def get_unique_words_count_user(m_cursor, id):
    """
    Returns distinct words count by user

    m_cursor: db.cursor()
    id: member id
    """
    m_cursor.execute("""
        SELECT COUNT(DISTINCT word)
        FROM words
        WHERE id = ?
        """, (id,))
    count = m_cursor.fetchone()[0]

    return count


def create_wordcloud(words, filename):
    """
    Creates and stores wordcloud for the server

    words: dictionary containing words as key and frequency as values
    filename: filename
    """

    # server icon based mask
    # create the wordcloud object
    wordcloud = WordCloud(
        random_state=1,
        mode="RGBA",
        margin=30,
        width=1600,
        height=1000,
        stopwords=STOPWORDS,
        max_words=70,
        font_path="./fonts/Montserrat-Bold.ttf"
    )

    # generate the wordcloud
    wordcloud.generate_from_frequencies(words)

    # graphic and file config
    plt.figure(figsize=(16, 10), facecolor='k')
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.savefig(f"wordcloud/{filename}.png", facecolor='k', bbox_inches='tight')
    plt.close('all')


class Wordcloud(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()

    @commands.command(aliases=["wcs", "wcserver"])
    async def wordcloudserver(self, ctx, length=2):
        """
        Returns a wordcloud that shows the most frequently used words in the server graphically.
        """
        filename = "worldcloud_server"
        m_DB = sqlite3.connect('messages.db')
        m_cursor = m_DB.cursor()
        samplesize = get_sample_size(m_cursor)
        samplesize_unique = get_unique_words_count(m_cursor)

        word_frequency = get_most_frequent_words(m_cursor, length)
        word_length_samplesize = get_word_count_length(m_cursor, length)
        create_wordcloud(dict(word_frequency), filename)

        file = discord.File(f"wordcloud/{filename}.png")  # an image in the same folder as the main bot file
        embed = discord.Embed(timestamp=ctx.message.created_at)
        embed.set_author(icon_url=ctx.guild.icon,
                         name=(
                             f"{ctx.guild.name} Wordcloud ({abbreviate_number(samplesize)} Words, "
                             f"{abbreviate_number(samplesize_unique)} Distinct)"
                         )
                         )
        embed.set_image(url=f"attachment://{filename}.png")
        embed.set_footer(
            text=(
                f"{abbreviate_number(word_length_samplesize)} ({round(word_length_samplesize/samplesize*100, 1)}%) "
                f"out of {abbreviate_number(samplesize)} Words had more than {length} Chars. "
            ))
        # filename and extension have to match (ex. "thisname.jpg" has to be "attachment://thisname.jpg")
        await ctx.send(embed=embed, file=file)

    @commands.command(aliases=["wc", "wcuser", "wordclouduser"])
    async def wordcloud(self, ctx, member: discord.Member = None):
        """
        Returns a wordcloud that shows the most frequently used words by a member graphically.
        """

        m_DB = sqlite3.connect('messages.db')
        m_cursor = m_DB.cursor()
        if member is None:
            member = ctx.author
        filename = f"word_cloud_{member.id}"
        user = member.id

        samplesize = get_sample_size_user(m_cursor, user)
        samplesize_unique = get_unique_words_count_user(m_cursor, user)

        word_frequency = get_most_frequent_words_user(m_cursor, user)
        create_wordcloud(dict(word_frequency), filename)

        file = discord.File(f"wordcloud/{filename}.png")  # an image in the same folder as the main bot file
        embed = discord.Embed(timestamp=ctx.message.created_at)
        embed.set_author(icon_url=member.avatar,
                         name=(
                             f"{member.name} ({abbreviate_number(samplesize)} Words, "
                             f"{abbreviate_number(samplesize_unique)} Distinct)")
                         )
        embed.set_image(url=f"attachment://{filename}.png")
        # filename and extension have to match (ex. "thisname.jpg" has to be "attachment://thisname.jpg")
        await ctx.send(embed=embed, file=file)

    @commands.command()
    async def said(self, ctx, word=None):
        """Returns leaderboard of members who most frequently used the word."""
        if word is None:
            await ctx.send("Please add a word.\n*vocablb **word**")
            return

        member = ctx.author
        user = member.id

        m_DB = sqlite3.connect('messages.db')
        m_cursor = m_DB.cursor()

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_thumbnail(url=ctx.guild.icon)
        word_count = get_word_frequency_server(m_cursor, word)

        topten_text = ""
        rank = 1
        top_10_total = 0

        author_word_count = get_word_frequency_user(m_cursor, user, word)

        for user, frequency in get_vocab_user(m_cursor, word):
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
    await bot.add_cog(Wordcloud(bot))
