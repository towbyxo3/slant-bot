
from discord.ext import commands, tasks
from utils import default
import datetime
import discord
import sqlite3
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import io
import os
import sys
from queries.userchatqueries import *
from queries.serverchatqueries import *
from helpers.dateformatting import *
from helpers.numberformatting import abbreviate_number

sys.path.append("queries")
sys.path.append("helpers")


def shorten_username(username, max_length=10):
    """
    Takes care of names that are too long to display on the leaderboard
    """
    if len(username) <= max_length:
        return username
    else:
        return username[:max_length - 2] + ".."


def top_20_monthly_chatters(cursor, year, month):
    """
    Returns top monthly chatters of a particular month in a year
    """
    cursor.execute("""
        SELECT Id, SUM(Msgs) AS Msgs
        FROM userchat
        WHERE strftime('%m', Date) = ? AND strftime('%Y', Date) = ?
        GROUP BY Id
        ORDER BY Msgs DESC
        Limit 20
        """, (month, year))
    rows = cursor.fetchall()
    return rows


def top_20_all_time_chatters(cursor):
    # returns top all time chatters
    cursor.execute("""
        SELECT ID, SUM(Msgs) AS Msgs
        FROM userchat
        GROUP BY ID
        ORDER BY SUM(Msgs) DESC
        LIMIT 20
        """)
    rows = cursor.fetchall()
    return rows


def get_day_of_month():
    now = datetime.datetime.now()
    return now.day


def get_prev_month():
    now = datetime.datetime.now()
    first_day_of_month = datetime.datetime(now.year, now.month, 1)
    prev_month_last_day = first_day_of_month - datetime.timedelta(days=1)
    year = str(prev_month_last_day.year)
    month = prev_month_last_day.strftime("%m")
    return month, year


class MonthlyLeaderboardUpdate(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.channel_monthly_leaderboard_update = self.config["channel_monthly_leaderboard_update"]
        self.channel_all_time_leaderboard_update = self.config["channel_all_time_leaderboard_update"]
        self.my_guild = self.config["my_guild"]

    @commands.Cog.listener()
    async def on_ready(self):
        self.monthly_leaderboard_update.start()
        self.alltime_leaderboard_update.start()

    @tasks.loop(hours=24)
    async def monthly_leaderboard_update(self):
        """
        This task checks once a day wheither todays day is the 1st day
        of the month. If thats the case, a leaderboard picture of
        previous month is created and posted in a dedicated channel.
        """
        day_of_the_month = 1
        if get_day_of_month() != day_of_the_month:
            return

        CHANNEL_ID = self.channel_all_time_leaderboard_update
        SERVER_ID = self.my_guild
        FONT_PATH = "fonts/Montserrat-Bold.ttf"
        FONT_PATH_TITLE = "fonts/Montserrat-VariableFont_wght.ttf"

        # fetch channel object where the leaderboard gets posted
        channel = self.bot.get_channel(CHANNEL_ID)
        month, year = get_prev_month()
        month = "01"

        # fetch server object in order to obtain its avatar/icon
        server = await self.bot.fetch_guild(SERVER_ID)
        server_av = server.icon

        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        # set y offsets for top 3 and top 4-10 rows
        Y_OFFSET = 460
        Y_OFFSET_PODIUM = 460
        PODIUM_COLORS = [
            (255, 215, 0),      # GOLD
            (192, 192, 192),    # SILVER
            (205, 127, 50),     # BRONZE
        ]
        # HERE YOU CAN SELECT YOUR BASE IMAGE YOURSELF !
        BASE_IMAGE = Image.open(f"base_images/leaderboard_message/{month}.png")
        BASE_IMAGE = BASE_IMAGE.resize((2560, 1440))

        rank = 1
        for id, msgs in top_20_monthly_chatters(c_cursor, year, month):
            # errors related to fetching a non existing user are caught
            # and makes the for loop skip to the next user(id)
            try:
                above_top_10 = rank < 11
                if rank == 11:
                    Y_OFFSET = 460
                # fetch member object with id and get avatar url
                print(id)
                member = await self.bot.fetch_user(id)
                print(member.name)
                avatar_url = member.display_avatar

                # download avatar and resize it (top 3 has bigger avatars)
                avatar_response = requests.get(avatar_url)
                avatar_image = Image.open(io.BytesIO(avatar_response.content)).convert("RGB")
                avatar_size = 300 if rank < 4 else (125 if above_top_10 else 75)
                avatar_image = avatar_image.resize((avatar_size, avatar_size))

                # create circular version of the avatar
                mask = Image.new("L", avatar_image.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + avatar_image.size, fill=255)
                avatar_image = ImageOps.fit(avatar_image, mask.size, centering=(0.5, 0.5))
                avatar_image.putalpha(mask)
                outline_image = Image.new("RGBA", avatar_image.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(outline_image)

                # circular picture gets pasted onto the base image,
                # a podium color will be added to the top 3
                if rank > 3:
                    BASE_IMAGE.paste(
                        avatar_image,
                        (1450 if above_top_10 else 2100, Y_OFFSET),
                        mask=mask
                    )
                    draw = ImageDraw.Draw(BASE_IMAGE)

                    # member name text
                    font_member_podium = ImageFont.truetype(FONT_PATH, 65 if above_top_10 else 40)
                    draw.text(
                        (1600 if above_top_10 else 2200, (70 if above_top_10 else 40) + Y_OFFSET),
                        f"{rank}.{shorten_username(member.name)}",
                        font=font_member_podium,
                        fill=(255, 255, 255),
                        anchor="ls"
                    )

                    # messages count text
                    font_messages_podium = ImageFont.truetype(FONT_PATH, 40 if above_top_10 else 30)
                    draw.text(
                        (1600 if above_top_10 else 2200, (115 if above_top_10 else 71) + Y_OFFSET),
                        f"{abbreviate_number(msgs)} Messages",
                        font=font_messages_podium,
                        fill=(255, 255, 255),
                        anchor="ls"
                    )

                    Y_OFFSET += 140 if above_top_10 else 98
                else:
                    # podium coloured border is added to the circular avatar
                    draw.ellipse(
                        (0, 0) + avatar_image.size,
                        outline=PODIUM_COLORS[rank - 1],
                        width=10)
                    avatar_outline_image = Image.alpha_composite(avatar_image, outline_image)

                    BASE_IMAGE.paste(
                        avatar_outline_image,
                        (50, Y_OFFSET_PODIUM),
                        mask=mask
                    )
                    draw = ImageDraw.Draw(BASE_IMAGE)

                    font_name = ImageFont.truetype(FONT_PATH, 130)
                    draw.text(
                        (400, 150 + Y_OFFSET_PODIUM),
                        f"{rank}.{shorten_username(member.name, 10)}",
                        font=font_name,
                        fill=PODIUM_COLORS[rank - 1],
                        anchor="ls"
                    )

                    font_messages = ImageFont.truetype(FONT_PATH, 85)
                    draw.text(
                        (400, 255 + Y_OFFSET_PODIUM),
                        f"{msgs} Messages",
                        font=font_messages,
                        fill=(255, 255, 255),
                        anchor="ls"
                    )

                    Y_OFFSET_PODIUM += 323
            except Exception as e:
                print(e)
                rank -= 1
            rank += 1

        try:
            # month year text
            font_month = ImageFont.truetype(FONT_PATH_TITLE, 150)
            draw.text(
                (2530, 150),
                f"{get_month_name(month)} {year}",
                font=font_month,
                fill=(255, 255, 255),
                stroke_fill=(255, 255, 255),
                stroke_width=3,
                anchor="rs"
            )

            # server name text
            font_server_name = ImageFont.truetype(FONT_PATH_TITLE, 150)
            draw.text(
                (250, 150),
                server.name,
                font=font_server_name,
                fill=(255, 255, 255),
                stroke_fill=(255, 255, 255),
                stroke_width=3,
                anchor="ls"
            )

            # unique chatters count text
            unique_chatters_month = get_distinct_chatters_count_month(c_cursor, year, month)
            monthly_server_msgs, monthly_server_chars = get_monthly_server_msgs(c_cursor, year, month)
            font_server_stats = ImageFont.truetype(FONT_PATH_TITLE, 95)
            draw.text(
                (50, 270),
                f"{unique_chatters_month} Chatters",
                font=font_server_stats,
                fill=(255, 255, 255),
                stroke_fill=(255, 255, 255),
                stroke_width=3,
                anchor="ls"
            )
            # messages count text
            draw.text(
                (50, 370),
                f"{abbreviate_number(monthly_server_msgs)} Messages",
                font=font_server_stats,
                fill=(255, 255, 255),
                stroke_fill=(255, 255, 255),
                stroke_width=3,
                anchor="ls"
            )

            # Download the server's avatar and create a circular version of it
            avatar_response = requests.get(server_av)
            avatar_image = Image.open(io.BytesIO(avatar_response.content))
            avatar_image = avatar_image.convert("RGB")
            avatar_image = avatar_image.resize((150, 150))
            mask = Image.new("L", avatar_image.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + avatar_image.size, fill=255)
            avatar_image = ImageOps.fit(avatar_image, mask.size, centering=(0.5, 0.5))
            avatar_image.putalpha(mask)

            # Create a new image to draw the outline on
            outline_image = Image.new("RGBA", avatar_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(outline_image)

            # Draw an outline around the circular avatar
            draw.ellipse(
                (0, 0) + avatar_image.size,
                outline=(255, 255, 255),
                width=5
            )
            avatar_outline_image = Image.alpha_composite(avatar_image, outline_image)
            BASE_IMAGE.paste(
                avatar_outline_image,
                (50, 15),
                mask=mask
            )
            draw = ImageDraw.Draw(BASE_IMAGE)

            # Save the final image
            BASE_IMAGE.save("base_images/monthly_leaderboard.png")

            await channel.send(file=discord.File("base_images/monthly_leaderboard.png"))

            # delete created leaderboard picture after it was sent to the channel
            os.remove("base_images/monthly_leaderboard.png")
        except Exception as e:
            print(e)

    @tasks.loop(hours=24)
    async def alltime_leaderboard_update(self):
        """
        All-Time messages leaderboard update every month
        """

        day_of_the_month = 1
        if get_day_of_month() != 9:
            return
        CHANNEL_ID = self.channel_all_time_leaderboard_update
        SERVER_ID = self.my_guild
        FONT_PATH = "fonts/Montserrat-Bold.ttf"
        FONT_PATH_TITLE = "fonts/Montserrat-VariableFont_wght.ttf"
        # fetch channel object where the leaderboard gets posted
        channel = self.bot.get_channel(CHANNEL_ID)
        month, year = get_prev_month()

        # fetch server object in order to obtain its avatar/icon
        server = await self.bot.fetch_guild(SERVER_ID)
        server_av = server.icon

        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        # set y offsets for top 3 and top 4-10 rows
        Y_OFFSET = 460
        Y_OFFSET_PODIUM = 460
        PODIUM_COLORS = [
            (255, 215, 0),      # GOLD
            (192, 192, 192),    # SILVER
            (205, 127, 50),     # BRONZE
        ]
        # HERE YOU CAN SELECT YOUR BASE IMAGE YOURSELF !
        # BASE_IMAGE = Image.open(f"base_images/leaderboard_message/{month}.png")
        BASE_IMAGE = Image.open(f"base_images/leaderboard_message/00.png")
        BASE_IMAGE = BASE_IMAGE.resize((2560, 1440))

        rank = 1
        for id, msgs in top_20_all_time_chatters(c_cursor):
            try:

                above_top_10 = rank < 11
                if rank == 11:
                    Y_OFFSET = 460
                # fetch member object with id and get avatar url
                member = await self.bot.fetch_user(id)

                avatar_url = member.display_avatar

                # download avatar and resize it (top 3 has bigger avatars)
                avatar_response = requests.get(avatar_url)
                avatar_image = Image.open(io.BytesIO(avatar_response.content)).convert("RGB")
                avatar_size = 300 if rank < 4 else (125 if above_top_10 else 75)
                avatar_image = avatar_image.resize((avatar_size, avatar_size))

                # create circular version of the avatar
                mask = Image.new("L", avatar_image.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + avatar_image.size, fill=255)
                avatar_image = ImageOps.fit(avatar_image, mask.size, centering=(0.5, 0.5))
                avatar_image.putalpha(mask)
                outline_image = Image.new("RGBA", avatar_image.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(outline_image)

                # circular picture gets pasted onto the base image,
                # a podium color will be added to the top 3
                if rank > 3:
                    BASE_IMAGE.paste(
                        avatar_image,
                        (1450 if above_top_10 else 2100, Y_OFFSET),
                        mask=mask
                    )
                    draw = ImageDraw.Draw(BASE_IMAGE)

                    # member name text
                    font_member_podium = ImageFont.truetype(FONT_PATH, 65 if above_top_10 else 40)
                    draw.text(
                        (1600 if above_top_10 else 2200, (70 if above_top_10 else 40) + Y_OFFSET),
                        f"{rank}.{shorten_username(member.name)}",
                        font=font_member_podium,
                        fill=(255, 255, 255),
                        anchor="ls"
                    )

                    # messages count text
                    font_messages_podium = ImageFont.truetype(FONT_PATH, 40 if above_top_10 else 30)
                    draw.text(
                        (1600 if above_top_10 else 2200, (115 if above_top_10 else 71) + Y_OFFSET),
                        f"{abbreviate_number(msgs)} Messages",
                        font=font_messages_podium,
                        fill=(255, 255, 255),
                        anchor="ls"
                    )

                    Y_OFFSET += 140 if above_top_10 else 98
                else:
                    # podium coloured border is added to the circular avatar
                    draw.ellipse(
                        (0, 0) + avatar_image.size,
                        outline=PODIUM_COLORS[rank - 1],
                        width=10)
                    avatar_outline_image = Image.alpha_composite(avatar_image, outline_image)

                    BASE_IMAGE.paste(
                        avatar_outline_image,
                        (50, Y_OFFSET_PODIUM),
                        mask=mask
                    )
                    draw = ImageDraw.Draw(BASE_IMAGE)

                    font_name = ImageFont.truetype(FONT_PATH, 130)
                    draw.text(
                        (400, 150 + Y_OFFSET_PODIUM),
                        f"{rank}.{shorten_username(member.name, 10)}",
                        font=font_name,
                        fill=PODIUM_COLORS[rank - 1],
                        anchor="ls"
                    )

                    font_messages = ImageFont.truetype(FONT_PATH, 85)
                    draw.text(
                        (400, 255 + Y_OFFSET_PODIUM),
                        f"{msgs} Messages",
                        font=font_messages,
                        fill=(255, 255, 255),
                        anchor="ls"
                    )

                    Y_OFFSET_PODIUM += 323
            except Exception as e:
                print(e)
                rank -= 1
            rank += 1

        # all time text
        font_all_time = ImageFont.truetype(FONT_PATH_TITLE, 150)
        draw.text(
            (2530, 150),
            f"ALL-TIME",
            font=font_all_time,
            fill=(255, 255, 255),
            stroke_fill=(255, 255, 255),
            stroke_width=3,
            anchor="rs"
        )

        # month year text
        today = datetime.datetime.today()
        date_string = today.strftime('%d. %B %Y')
        font_month = ImageFont.truetype(FONT_PATH_TITLE, 45)
        draw.text(
            (2530, 270),
            f"As of {date_string}",
            font=font_month,
            fill=(255, 255, 255),
            stroke_fill=(255, 255, 255),
            stroke_width=3,
            anchor="rs"
        )

        # server name text
        font_server_name = ImageFont.truetype(FONT_PATH_TITLE, 150)
        draw.text(
            (250, 150),
            server.name,
            font=font_server_name,
            fill=(255, 255, 255),
            stroke_fill=(255, 255, 255),
            stroke_width=3,
            anchor="ls"
        )

        # unique chatters count text
        unique_chatters_all_time = get_distinct_chatters_count_alltime(c_cursor)
        all_time_server_msgs, all_time_server_chars = get_alltime_server_msgs(c_cursor)
        font_server_stats = ImageFont.truetype(FONT_PATH_TITLE, 95)
        draw.text(
            (50, 270),
            f"{unique_chatters_all_time} Chatters",
            font=font_server_stats,
            fill=(255, 255, 255),
            stroke_fill=(255, 255, 255),
            stroke_width=3,
            anchor="ls"
        )
        # messages count text
        draw.text(
            (50, 370),
            f"{abbreviate_number(all_time_server_msgs)} Messages",
            font=font_server_stats,
            fill=(255, 255, 255),
            stroke_fill=(255, 255, 255),
            stroke_width=3,
            anchor="ls"
        )

        # Download the server's avatar and create a circular version of it
        avatar_response = requests.get(server_av)
        avatar_image = Image.open(io.BytesIO(avatar_response.content))
        avatar_image = avatar_image.convert("RGB")
        avatar_image = avatar_image.resize((150, 150))
        mask = Image.new("L", avatar_image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + avatar_image.size, fill=255)
        avatar_image = ImageOps.fit(avatar_image, mask.size, centering=(0.5, 0.5))
        avatar_image.putalpha(mask)

        # Create a new image to draw the outline on
        outline_image = Image.new("RGBA", avatar_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(outline_image)

        # Draw an outline around the circular avatar
        draw.ellipse(
            (0, 0) + avatar_image.size,
            outline=(255, 255, 255),
            width=5
        )
        avatar_outline_image = Image.alpha_composite(avatar_image, outline_image)
        BASE_IMAGE.paste(
            avatar_outline_image,
            (50, 15),
            mask=mask
        )
        draw = ImageDraw.Draw(BASE_IMAGE)

        # Save the final image
        BASE_IMAGE.save("base_images/all_time_leaderboard.png")

        await channel.send(file=discord.File("base_images/all_time_leaderboard.png"))

        # delete created leaderboard picture after it was sent to the channel
        os.remove("base_images/all_time_leaderboard.png")

    @commands.command()
    async def leaderboardhistory(self, ctx):
        """
        This command goes through every month year combination and
        checks if theres chat data. If theres data, a leaderboard will
        be created. This command takes a while to finish because every
        single member has to be fetched one by one and the discord API
        is rate limited and slow.
        """

        CHANNEL_ID = ctx.channel.id
        SERVER_ID = self.my_guild
        FONT_PATH = "fonts/Montserrat-Bold.ttf"
        FONT_PATH_TITLE = "fonts/Montserrat-VariableFont_wght.ttf"
        # fetch channel object where the leaderboard gets posted
        channel = self.bot.get_channel(CHANNEL_ID)

        # fetch server object in order to obtain its avatar/icon
        server = await self.bot.fetch_guild(SERVER_ID)
        server_av = server.icon

        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()
        month, year = get_prev_month()

        # set y offsets for top 3 and top 4-10 rows
        PODIUM_COLORS = [
            (255, 215, 0),      # GOLD
            (192, 192, 192),    # SILVER
            (205, 127, 50),     # BRONZE
        ]

        for year in range(2015, int(year) + 1):
            year = str(year)
            for month in range(1, 13):
                month = f"{month:02d}"
                Y_OFFSET = 460
                Y_OFFSET_PODIUM = 460
                # HERE YOU CAN SELECT YOUR BASE IMAGE YOURSELF !
                BASE_IMAGE = Image.open(f"base_images/leaderboard_message/{month}.png")
                BASE_IMAGE = BASE_IMAGE.resize((2560, 1440))

                rank = 1

                for id, msgs in top_20_monthly_chatters(c_cursor, year, month):
                    try:
                        above_top_10 = rank < 11
                        if rank == 11:
                            Y_OFFSET = 460
                        # fetch member object with id and get avatar url
                        member = await self.bot.fetch_user(id)
                        print(member.name)
                        avatar_url = member.display_avatar

                        # download avatar and resize it (top 3 has bigger avatars)
                        avatar_response = requests.get(avatar_url)
                        avatar_image = Image.open(io.BytesIO(avatar_response.content)).convert("RGB")
                        avatar_size = 300 if rank < 4 else (125 if above_top_10 else 75)
                        avatar_image = avatar_image.resize((avatar_size, avatar_size))

                        # create circular version of the avatar
                        mask = Image.new("L", avatar_image.size, 0)
                        draw = ImageDraw.Draw(mask)
                        draw.ellipse((0, 0) + avatar_image.size, fill=255)
                        avatar_image = ImageOps.fit(avatar_image, mask.size, centering=(0.5, 0.5))
                        avatar_image.putalpha(mask)
                        outline_image = Image.new("RGBA", avatar_image.size, (0, 0, 0, 0))
                        draw = ImageDraw.Draw(outline_image)

                        # circular picture gets pasted onto the base image,
                        if rank > 3:    # top 4-20
                            BASE_IMAGE.paste(
                                avatar_image,
                                (1450 if above_top_10 else 2100, Y_OFFSET),
                                mask=mask
                            )
                            draw = ImageDraw.Draw(BASE_IMAGE)

                            # member name text
                            font_member_podium = ImageFont.truetype(FONT_PATH, 65 if above_top_10 else 40)
                            draw.text(
                                (1600 if above_top_10 else 2200, (70 if above_top_10 else 40) + Y_OFFSET),
                                f"{rank}.{shorten_username(member.name)}",
                                font=font_member_podium,
                                fill=(255, 255, 255),
                                anchor="ls"
                            )

                            # messages count text
                            font_messages_podium = ImageFont.truetype(FONT_PATH, 40 if above_top_10 else 30)
                            draw.text(
                                (1600 if above_top_10 else 2200, (115 if above_top_10 else 71) + Y_OFFSET),
                                f"{abbreviate_number(msgs)} Messages",
                                font=font_messages_podium,
                                fill=(255, 255, 255),
                                anchor="ls"
                            )

                            Y_OFFSET += 140 if above_top_10 else 98
                        else:   # top 3
                            # podium coloured border is added to the circular avatar
                            draw.ellipse(
                                (0, 0) + avatar_image.size,
                                outline=PODIUM_COLORS[rank - 1],
                                width=10)
                            avatar_outline_image = Image.alpha_composite(avatar_image, outline_image)

                            BASE_IMAGE.paste(
                                avatar_outline_image,
                                (50, Y_OFFSET_PODIUM),
                                mask=mask
                            )
                            draw = ImageDraw.Draw(BASE_IMAGE)

                            font_name = ImageFont.truetype(FONT_PATH, 130)
                            draw.text(
                                (400, 150 + Y_OFFSET_PODIUM),
                                f"{rank}.{shorten_username(member.name, 10)}",
                                font=font_name,
                                fill=PODIUM_COLORS[rank - 1],
                                anchor="ls"
                            )

                            font_messages = ImageFont.truetype(FONT_PATH, 85)
                            draw.text(
                                (400, 255 + Y_OFFSET_PODIUM),
                                f"{msgs} Messages",
                                font=font_messages,
                                fill=(255, 255, 255),
                                anchor="ls"
                            )

                            Y_OFFSET_PODIUM += 323
                    except Exception as e:
                        print(e)
                        rank -= 1
                    rank += 1

                # catches errors related to faulty base image and
                # no data entries for that particular month
                try:
                    # month year text
                    font_month = ImageFont.truetype(FONT_PATH_TITLE, 150)
                    draw.text(
                        (2530, 150),
                        f"{get_month_name(month)} {year}",
                        font=font_month,
                        fill=(255, 255, 255),
                        stroke_fill=(255, 255, 255),
                        stroke_width=3,
                        anchor="rs"
                    )

                    # server name text
                    font_server_name = ImageFont.truetype(FONT_PATH_TITLE, 150)
                    draw.text(
                        (250, 150),
                        server.name,
                        font=font_server_name,
                        fill=(255, 255, 255),
                        stroke_fill=(255, 255, 255),
                        stroke_width=3,
                        anchor="ls"
                    )

                    # unique chatters count text
                    unique_chatters_month = get_distinct_chatters_count_month(c_cursor, year, month)
                    monthly_server_msgs, monthly_server_chars = get_monthly_server_msgs(c_cursor, year, month)
                    font_server_stats = ImageFont.truetype(FONT_PATH_TITLE, 95)

                    draw.text(
                        (50, 270),
                        f"{unique_chatters_month} Chatters",
                        font=font_server_stats,
                        fill=(255, 255, 255),
                        stroke_fill=(255, 255, 255),
                        stroke_width=3,
                        anchor="ls"
                    )
                    # messages count text
                    draw.text(
                        (50, 370),
                        f"{abbreviate_number(monthly_server_msgs)} Messages",
                        font=font_server_stats,
                        fill=(255, 255, 255),
                        stroke_fill=(255, 255, 255),
                        stroke_width=3,
                        anchor="ls"
                    )

                    # Download the server's avatar and create a circular version of it
                    avatar_response = requests.get(server_av)
                    avatar_image = Image.open(io.BytesIO(avatar_response.content))
                    avatar_image = avatar_image.convert("RGB")
                    avatar_image = avatar_image.resize((150, 150))
                    mask = Image.new("L", avatar_image.size, 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0) + avatar_image.size, fill=255)
                    avatar_image = ImageOps.fit(avatar_image, mask.size, centering=(0.5, 0.5))
                    avatar_image.putalpha(mask)

                    # Create a new image to draw the outline on
                    outline_image = Image.new("RGBA", avatar_image.size, (0, 0, 0, 0))
                    draw = ImageDraw.Draw(outline_image)

                    # Draw an outline around the circular avatar
                    draw.ellipse(
                        (0, 0) + avatar_image.size,
                        outline=(255, 255, 255),
                        width=5
                    )
                    avatar_outline_image = Image.alpha_composite(avatar_image, outline_image)
                    BASE_IMAGE.paste(
                        avatar_outline_image,
                        (50, 15),
                        mask=mask
                    )
                    draw = ImageDraw.Draw(BASE_IMAGE)

                    # Save the final image
                    BASE_IMAGE.save(f"base_images/{year}-{month}.png")

                    await channel.send(file=discord.File(f"base_images/{year}-{month}.png"))

                    # delete created leaderboard picture after it was sent to the channel
                    # os.remove("base_images/leaderboard_message_custom.png")
                except Exception as e:
                    print(e)


async def setup(bot):
    await bot.add_cog(MonthlyLeaderboardUpdate(bot))
