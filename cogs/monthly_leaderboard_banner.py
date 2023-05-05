
from discord.ext import commands, tasks
from utils import default
import datetime
import discord
from PIL import Image
import sqlite3
import random
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import io
import os
import sys
from queries.userchatqueries import *
from queries.serverchatqueries import *
from helpers.dateformatting import *
from helpers.numberformatting import *

sys.path.append("queries")
sys.path.append("helpers")


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

    @commands.Cog.listener()
    async def on_ready(self):
        self.leaderboardupdates.start()

    @tasks.loop(hours=24)
    async def leaderboardupdates(self):
        # will later be changed to != 1
        # it posts a leaderboard of the previous month on the 1st day of the month
        if get_day_of_month() != 5:
            return

        # fetch channel object where the leaderboard gets posted
        channel = self.bot.get_channel(1057132842259325029)
        month, year = get_prev_month()

        # fetch server object in order to obtain its avatar/icon
        server = await self.bot.fetch_guild(1085334522440188015)
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
        BASE_IMAGE = Image.open("welcome_base_images/leaderboard_base.jpg")

        for rank, (id, msgs) in enumerate(TopMonthly(c_cursor, year, month), 1):
            # fetch member object with id and get avatar url
            member = await self.bot.fetch_user(id)
            avatar_url = member.display_avatar

            # download avatar and resize it (top 3 has bigger avatars)
            avatar_response = requests.get(avatar_url)
            avatar_image = Image.open(io.BytesIO(avatar_response.content)).convert("RGB")
            avatar_size = 125 if rank > 3 else 300
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
                    (1650, Y_OFFSET),
                    mask=mask
                )
                draw = ImageDraw.Draw(BASE_IMAGE)

                # member name text
                font_member_podium = ImageFont.truetype("arial.ttf", 65)
                draw.text(
                    (1800, 65 + Y_OFFSET),
                    f"{rank}. {member.name}#{member.discriminator}",
                    font=font_member_podium,
                    fill=(255, 255, 255),
                    anchor="ls"
                )

                # messages count text
                font_messages_podium = ImageFont.truetype("arial.ttf", 40)
                draw.text(
                    (1800, 110 + Y_OFFSET),
                    f"{abbreviate_number(msgs)} Messages",
                    font=font_messages_podium,
                    fill=(255, 255, 255),
                    anchor="ls"
                )

                Y_OFFSET += 140
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

                font_name = ImageFont.truetype("arial.ttf", 130)
                draw.text(
                    (400, 130 + Y_OFFSET_PODIUM),
                    f"{rank}. {member.name}#{member.discriminator}",
                    font=font_name,
                    fill=(255, 255, 255),
                    anchor="ls"
                )

                font_messages = ImageFont.truetype("arial.ttf", 85)
                draw.text(
                    (400, 235 + Y_OFFSET_PODIUM),
                    f"{msgs} Messages",
                    font=font_messages,
                    fill=(255, 255, 255),
                    anchor="ls"
                )

                font_messages = ImageFont.truetype("arial.ttf", 85)
                draw.text(
                    (400, 235 + Y_OFFSET_PODIUM),
                    f"{msgs} Messages",
                    font=font_messages,
                    fill=(255, 255, 255),
                    anchor="ls"
                )

                Y_OFFSET_PODIUM += 320

        # month name text
        font_month = ImageFont.truetype("arial.ttf", 220)
        draw.text(
            (50, 350),
            f"{get_month_name(month)} {year}",
            font=font_month,
            fill=(255, 255, 255),
            anchor="ls"
        )

        # server name text
        font_server_name = ImageFont.truetype("arial.ttf", 150)
        draw.text(
            (250, 150),
            server.name,
            font=font_server_name,
            fill=(255, 255, 255),
            anchor="ls"
        )

        # unique chatters count text
        unique_chatters_month = distinctChattersMonth(c_cursor, year, month)
        monthly_server_msgs, monthly_server_chars = monthlyServerMessages(c_cursor, year, month)
        font_server_stats = ImageFont.truetype("arial.ttf", 95)
        draw.text(
            (1650, 300),
            f"{unique_chatters_month} Chatters",
            font=font_server_stats,
            fill=(255, 255, 255),
            anchor="ls"
        )
        # messages count text
        draw.text(
            (1650, 180),
            f"{abbreviate_number(monthly_server_msgs)} Messages",
            font=font_server_stats,
            fill=(255, 255, 255),
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
            (50, 30),
            mask=mask
        )
        draw = ImageDraw.Draw(BASE_IMAGE)

        # Save the final image
        BASE_IMAGE.save("welcome_base_images/custom_image.png")

        await channel.send(file=discord.File("welcome_base_images/custom_image.png"))


async def setup(bot):
    await bot.add_cog(MonthlyLeaderboardUpdate(bot))
