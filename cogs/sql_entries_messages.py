import discord
import datetime
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from utils import default
from discord.ext import commands
import sqlite3
import re


def m_create_table(m_cursor):
    m_cursor.execute("""
        CREATE TABLE IF NOT EXISTS
                words(
                    ID TEXT,
                    word TEXT
                )
        """)


def m_snipe_create_table(m_cursor):
    m_cursor.execute("""
        CREATE TABLE IF NOT EXISTS
            deleted(
                ID TEXT,
                date TEXT,
                message TEXT,
                channel TEXT
            )
        """)


def m_edit_create_table(m_cursor):
    m_cursor.execute("""
        CREATE TABLE IF NOT EXISTS
            edited(
                ID TEXT,
                date_before TEXT,
                date_after TEXT,
                before_message TEXT,
                after_message TEXT,
                channel TEXT)
        """)


def m_data_entry(m_cursor, m_DB, user, list_of_words):
    for word in list_of_words:
        m_cursor.execute('INSERT INTO words VALUES(?, ?)', (user, word))
        m_DB.commit()


def m_snipe_data_entry(m_cursor, m_DB, id, date, message, channel):
    m_cursor.execute('INSERT INTO deleted VALUES(?, ?, ?, ?)',
                     (id, date, message, channel))
    m_DB.commit()


def m_edit_data_entry(m_cursor, m_DB, id, date_before, date_after, before, after,
                    channel):
    m_cursor.execute('INSERT INTO edited VALUES(?, ?, ?, ?, ?, ?)',
                     (id, date_before, date_after, before, after, channel))
    m_DB.commit()


def m_edit_get_last(m_cursor, m_db, channel):
    m_cursor.execute("""
        SELECT *
        FROM edited
        WHERE channel = ?
        ORDER BY ROWID DESC
        LIMIT 1
        """, (channel,))
    data = m_cursor.fetchall()
    if len(data) == 0:
        return None
    return data[0]


def m_snipe_get_last(m_cursor, m_db, channel, user=None):
    if user is None:
        m_cursor.execute("""
            SELECT *
            FROM deleted
            WHERE channel = ?
            ORDER BY ROWID DESC
            LIMIT 1
            """, (channel,))
    else:
        m_cursor.execute("""
            SELECT *
            FROM deleted
            WHERE channel = ? AND id = ?
            ORDER BY ROWID DESC
            LIMIT 1
            """, (channel, user))
    data = m_cursor.fetchall()
    if len(data) == 0:
        return None
    return data[0]


def extract_words(string):
    # Remove any URLs from the string
    string = re.sub(r'https?://\S+', '', string)

    # Split the string into words
    words = string.split()

    # Return a list of upperwords that contain only letters
    return [
        word.rstrip('!?.,').upper() for word in words if word[0] != '*'
    ]


def readable_timedelta(timestamp1, timestamp2):
    # Parse the timestamps and convert them to datetime objects
    datetime1 = datetime.strptime(timestamp1, "%Y-%m-%d %H:%M:%S.%f")
    datetime2 = datetime.strptime(timestamp2, "%Y-%m-%d %H:%M:%S.%f")

    # Calculate the difference between the datetime objects using the relativedelta method
    delta = relativedelta(datetime1, datetime2)

    # Format the timedelta in a readable form and remove the parts with 0
    output = f"{delta.days} day" if delta.days == 1 else f"{delta.days} days" if delta.days > 0 else ""
    if delta.days > 1:
        return output
    output += f" {delta.hours} hr" if delta.hours == 1 else f" {delta.hours} hrs" if delta.hours > 0 else ""
    output += f" {delta.minutes} min" if delta.minutes == 1 else f" {delta.minutes} mins" if delta.minutes > 0 else ""
    output += f" {delta.seconds} sec" if delta.seconds == 1 else f" {delta.seconds} secs" if delta.seconds > 0 else ""
    return output


def print_time_difference(timestamp_str):
    # Parse the input string to a datetime object
    timestamp = datetime.fromisoformat(timestamp_str)

    # Get the current time in UTC
    now = datetime.now(timezone.utc)

    # Calculate the time difference
    try:

        time_diff = now - timestamp
    except:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
        time_diff = now - timestamp

    # Convert the time difference to seconds
    seconds = time_diff.total_seconds()

    # Convert the seconds to a human-readable form
    if seconds < 60:
        return (f'{int(seconds)} sec ago' if int(seconds) == 1 else f'{int(seconds)} secs ago')
    elif seconds < 3600:
        return (f'{int(seconds / 60)} min ago' if int(seconds / 60) == 1 else f'{int(seconds / 60)} mins ago')
    elif seconds < 86400:
        return (f'{int(seconds / 3600)} hour ago' if int(seconds / 3600) == 1 else f'{int(seconds / 3600)} hours ago')
    else:
        return (f'{int(seconds / 86400)} day ago' if int(seconds / 86400) == 1 else f'{int(seconds / 86400)} days ago')


def m_name_history_create_table(m_cursor):
    m_cursor.execute("""
        CREATE TABLE IF NOT EXISTS
            namehistory(
                Date DATE,
                Id INTEGER,
                name TEXT,
                UNIQUE (Id, name)
            )
        """)


def m_name_history_entry(m_cursor, m_DB, date, id, name):
    m_cursor.execute('INSERT OR IGNORE INTO namehistory VALUES(?, ?, ?)', (date, id, name))
    m_DB.commit()


class MessageEntries(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and not message.content.startswith('*') and message.channel.id == 1085356879410102363:
            m_DB = sqlite3.connect('messages.db')
            m_cursor = m_DB.cursor()
            user = message.author.id
            list_of_words = extract_words(message.content)
            m_create_table(m_cursor)
            m_data_entry(m_cursor, m_DB, user, list_of_words)

            # new##
            date = datetime.now().strftime("%Y-%m-%d")
            name = str(message.author)
            nickname = str(message.author.display_name)

            m_name_history_create_table(m_cursor)
            m_name_history_entry(m_cursor, m_DB, date, user, name)
            m_name_history_entry(m_cursor, m_DB, date, user, nickname)

            mentionfilter = str(message.content).split()
            m_cursor.execute("""
                        CREATE TABLE IF NOT EXISTS mentions(
                           author INTEGER,
                           mention INTEGER,
                           count INTEGER,
                           UNIQUE (author, mention)
                           )
                        """)
            for w in mentionfilter:
                if w.startswith("<@") and w.endswith(">"):
                    m_cursor.execute("""
                        INSERT OR IGNORE INTO mentions
                        VALUES(?, ?, ?)
                        """, (message.author.id, w[2:-1], 0))
                    m_cursor.execute("""
                        UPDATE mentions
                        SET count = count + 1
                        WHERE author = ? AND mention = ?
                        """, (message.author.id, w[2:-1]))
            m_DB.commit()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        if len(message.content) >= 1:
            m_DB = sqlite3.connect('messages.db')
            m_cursor = m_DB.cursor()
            m_snipe_create_table(m_cursor)
            # Get the user who deleted the message
            date = str(message.created_at)
            author = message.author.id
            message_content = message.content
            channel = message.channel.id
            m_snipe_data_entry(m_cursor, m_DB, author, date, message_content,
                             channel)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
        if len(before.content) >= 1 and before.content != after.content:
            m_DB = sqlite3.connect('messages.db')
            m_cursor = m_DB.cursor()
            m_edit_create_table(m_cursor)
            date_before = str(before.created_at)[:26]
            date_after = str(datetime.utcnow())
            author = before.author.id
            message_content_before = before.content
            message_content_after = after.content
            channel = before.channel.id

            m_edit_data_entry(m_cursor, m_DB, author, date_before, date_after,
                              message_content_before, message_content_after,
                              channel)

    @commands.command()
    async def snip(self, ctx):
        m_DB = sqlite3.connect('messages.db')
        m_cursor = m_DB.cursor()

        try:
            id, date_before, date_after, before_content, after_content, channel = m_edit_get_last(m_cursor, m_DB, ctx.channel.id)
        except:
            embed = discord.Embed(color=discord.Color.blue(), description="No messages found")
            await ctx.send(embed=embed)
            return

        edited_after = readable_timedelta(date_after, date_before)

        sniped_user = await self.bot.fetch_user(id)

        time_deleted = print_time_difference(date_after)

        print(edited_after)

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_author(name=f"{sniped_user}   •   {time_deleted}", icon_url=sniped_user.avatar)
        # embed.add_field(name="User", value=f"<@{id}>")
        # embed.add_field(name="Channel", value=(f"<#{channel}>"))
        # embed.add_field(name="Edit time", value=edited_after + "\u200b")
        embed.add_field(name="Before", value=before_content, inline=False)
        embed.add_field(name="After", value=after_content, inline=False)

        # embed.set_footer(icon_url=ctx.author.avatar,
        embed.set_footer(text=f"Edit time: {edited_after} \u200b")
        # text=f"Sniped by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.command()
    async def snipe(self, ctx, member: discord.Member = None):
        # snipe description?
        m_DB = sqlite3.connect('messages.db')
        m_cursor = m_DB.cursor()

        try:
            if member is None:
                id, date, message, channel = m_snipe_get_last(m_cursor, m_DB, ctx.channel.id)
            else:
                id, date, message, channel = m_snipe_get_last(m_cursor, m_DB, ctx.channel.id, member.id)
        except:
            embed = discord.Embed(color=discord.Color.blue(), description="No messages found")
            await ctx.send(embed=embed)
            return

        time_deleted = print_time_difference(date)

        sniped_user = await self.bot.fetch_user(id)

        embed = discord.Embed(  # timestamp=ctx.message.created_at,
            color=discord.Color.blue(),
            description=message)
        embed.set_author(name=f"{sniped_user}   •   {time_deleted}", icon_url=sniped_user.avatar)

        # embed.set_footer(icon_url=ctx.author.avatar,text=f"Sniped by {ctx.author}")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(MessageEntries(bot))
