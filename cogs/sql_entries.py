import sqlite3


import discord
import psutil
import os

# import datetime
from datetime import datetime, timedelta
# from discord.ext.commands.context import Context
# from discord.ext.commands._types import BotT
from discord.ext import commands
# from discord.ext.commands import errors
from utils import default
# import time
import sqlite3
# import calendar


def sc_create_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS serverchat
            (Date DATE PRIMARY KEY,
             Msgs INTEGER,
             Chars INTEGER,
             Links INTEGER,
             Files INTEGER)
        """
                   )


def sc_data_entry(cursor, DB, date):
    cursor.execute("""
        INSERT OR IGNORE INTO serverchat VALUES(?, ?, ?, ?, ?)
        """, (date, 0, 0, 0, 0))
    DB.commit()


def sc_update(cursor, DB, chars, links, files, date):
    cursor.execute("""
        UPDATE serverchat
        SET msgs = msgs + 1,
            chars = chars + ?,
            links = links +?,
            files = files + ?
        WHERE date = ?
        """, (chars, links, files, date))
    DB.commit()


def uc_create_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS userchat(
            date DATE,
            ID INTEGER,
            msgs INTEGER,
            UNIQUE(date, ID))
        """)


def uc_data_entry(cursor, DB, date, user):
    cursor.execute("""
        INSERT OR IGNORE INTO userchat VALUES(?, ?, ?)
        """, (date, user, 0))
    DB.commit()


def uc_update(cursor, DB, date, user):
    cursor.execute("""
        UPDATE userchat
        SET msgs = msgs + 1
        WHERE ID = ? AND date = ?
        """, (user, date))
    DB.commit()

#####################################


def entry_message_timestamp(cursor, DB, user, timestamp, content):
    cursor.execute("""
        INSERT OR IGNORE INTO B40 VALUES(?, ?, ?)
        """, (user, timestamp, content))
    DB.commit()


class entries(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == 1085356879410102363:
            # CONNECT TO DATA BASES SC = SERVERCHAT, UC = USERCHAT
            c_DB = sqlite3.connect("chat.db")
            c_cursor = c_DB.cursor()

            # CREATE DATA THAT WILL BE STORED IN DATABASES
            user = message.author.id
            date = datetime.now().strftime("%Y-%m-%d")
            chars = len(message.clean_content)
            links = 1 if "http" in message.content.lower() else 0
            files = 1 if len(message.attachments) > 0 else 0

            # SERVERCHAT DB QUERIES
            sc_create_table(c_cursor)
            sc_data_entry(c_cursor, c_DB, date)
            sc_update(c_cursor, c_DB, chars, links, files, date)

            # USERCHAT DB QUERIES
            uc_create_table(c_cursor)
            uc_data_entry(c_cursor, c_DB, date, user)
            uc_update(c_cursor, c_DB, date, user)

            timestamp = str(datetime.now())[:19]
            content = message.content

            entry_message_timestamp(c_cursor, c_DB, user, timestamp, content)

            c_DB.close()


async def setup(bot):
    await bot.add_cog(entries(bot))
