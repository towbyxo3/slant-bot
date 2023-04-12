import sqlite3
import discord
from discord.ext import commands
from utils import default
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import sys
from helpers.numberformatting import abbreviate_number

sys.path.append("helpers")


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
    filtered_data = [(word, count) for word, count in data if not (word.startswith(
        '@') or word.startswith(':') or word.startswith('<') or word.startswith('#'))]

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
    filtered_data = [(word, count) for word, count in data if not (word.startswith('@') or word.startswith(':') or word.startswith('<') or word.startswith('#'))]

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


def create_word_cloud_server(words):
    """
    Creates and stores wordcloud for the server

    words: dictionary containing words as key and frequency as values
    """

    # server icon based mask
    mask = np.array(Image.open("wordcloud/B40.jpg"))

    # create the wordcloud object
    wordcloud = WordCloud(
        mask=mask,
        random_state=1,
        mode="RGBA",
        margin=15,
        width=1600,
        height=800,
        max_words=100,
        stopwords=STOPWORDS
    )

    # generate the wordcloud
    wordcloud.generate_from_frequencies(words)

    # graphic and file config
    plt.figure(figsize=(20, 10), facecolor='k')
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.savefig('wordcloud/wordcloud.png', facecolor='k', bbox_inches='tight')
    plt.close('all')


def create_wordcloud_user(words):
    """
    Creates and stores wordcloud for the server

    words: dictionary containing words as key and frequency as values
    """

    # server icon based mask
    # create the wordcloud object
    wordcloud = WordCloud(
        random_state=1,
        mode="RGBA",
        margin=30,
        width=1600,
        height=1000,
        max_words=70,
        stopwords=STOPWORDS
    )

    # generate the wordcloud
    wordcloud.generate_from_frequencies(words)

    # graphic and file config
    plt.figure(figsize=(16, 10), facecolor='k')
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.savefig('wordcloud/wordclouduser.png', facecolor='k', bbox_inches='tight')
    plt.close('all')


class wordcloud(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()

    @commands.command(aliases=["wcs", "wcserver"])
    async def wordcloudserver(self, ctx, length=3):
        m_DB = sqlite3.connect('messages.db')
        m_cursor = m_DB.cursor()
        samplesize = get_sample_size(m_cursor)
        samplesize_unique = get_unique_words_count(m_cursor)

        word_frequency = get_most_frequent_words(m_cursor, length)
        word_length_samplesize = get_word_count_length(m_cursor, length)
        create_word_cloud_server(dict(word_frequency))

        file = discord.File("wordcloud/wordcloud.png")  # an image in the same folder as the main bot file
        embed = discord.Embed(timestamp=ctx.message.created_at)
        embed.set_author(icon_url=ctx.guild.icon,
                         name=(
                             f"{ctx.guild.name} Wordcloud ({abbreviate_number(samplesize)} Words, "
                             f"{abbreviate_number(samplesize_unique)} Distinct)"
                         )
                         )
        embed.set_image(url="attachment://wordcloud.png")
        embed.set_footer(
            text=(
                f"{abbreviate_number(word_length_samplesize)} ({round(word_length_samplesize/samplesize*100, 1)}%) "
                f"out of {abbreviate_number(samplesize)} Words had more than {length} Chars. "
            ))
        # filename and extension have to match (ex. "thisname.jpg" has to be "attachment://thisname.jpg")
        await ctx.send(embed=embed, file=file)

    @commands.command(aliases=["wc", "wcuser", "wordclouduser"])
    async def wordcloud(self, ctx, member: discord.Member = None):
        m_DB = sqlite3.connect('messages.db')
        m_cursor = m_DB.cursor()
        if member is None:
            member = ctx.author
        user = member.id

        samplesize = get_sample_size_user(m_cursor, user)
        samplesize_unique = get_unique_words_count_user(m_cursor, user)

        word_frequency = get_most_frequent_words_user(m_cursor, user)
        create_wordcloud_user(dict(word_frequency))

        file = discord.File("wordcloud/wordclouduser.png")  # an image in the same folder as the main bot file
        embed = discord.Embed(timestamp=ctx.message.created_at)
        embed.set_author(icon_url=member.avatar,
                         name=(
                             f"{member.name} ({abbreviate_number(samplesize)} Words, "
                             f"{abbreviate_number(samplesize_unique)} Distinct)")
                         )
        embed.set_image(url="attachment://wordclouduser.png")
        # filename and extension have to match (ex. "thisname.jpg" has to be "attachment://thisname.jpg")
        await ctx.send(embed=embed, file=file)


async def setup(bot):
    await bot.add_cog(wordcloud(bot))
