import sqlite3
import discord
import psutil
import os
import datetime
from typing import Union
from discord.ext import commands
from utils import default
import calendar
import sys
from helpers.dateformatting import get_month_name
from helpers.numberformatting import abbreviate_number
from datascience.heatmapscripts import *
from queries.userchatqueries import *
from queries.serverchatqueries import *
from helpers.dateformatting import DbYYYformat
from datascience.chartscripts import create_chart_weekday, create_chart_month
from PIL import Image, ImageDraw, ImageFont
import asyncio
import time


sys.path.append("datascience")
sys.path.append("queries")
sys.path.append("helpers")


async def send_load_message(message, stage, stages):
    """
    Sends updated stage of the loading bar and returns new stage if
    loading hasnt finished yet

    message: message object that gets updated and eventually deleted
    stage: current stage
    stages:
    """
    stage += 1
    stages_left = stages - stage

    # create loading bar text using emojis
    loading_bar = f"Loading... {':green_square:' * stage}{':black_large_square:' * stages_left}"
    await message.edit(content=loading_bar)

    # we reached the last stage
    if stage == stages:
        await asyncio.sleep(1)
        await message.delete()
        return
    return stage


def create_rewind_gallery(who, year, server=False):
    """
    Creates a gallery out of the images in a directory sorted by creation date.

    who: guild or user whos data is showcased in the gallery
    year: showcased year
    server: wheither the gallery is for the server (else its for the user)
    """
    # create list of image filenames in the folder
    folder = f'rewind_images/{"server/" if server else "user/"}'
    image_files = [f for f in os.listdir(folder) if f.endswith(".png") or f.endswith(".gif")]

    # create a list of Image objects for each image file
    images = [Image.open(os.path.join(folder, file)) for file in image_files]

    title_space = 300
    divider_space = 150
    # create a new image with a width equal to the max width of the images and a height equal to the total height of all the images
    widths, heights = zip(*(i.size for i in images))
    max_width = max(widths)
    total_height = sum(heights) + title_space + divider_space
    new_im = Image.new('RGBA', (max_width, total_height), (0, 0, 0, 255))

    # sort the images by creation time
    image_files = sorted(image_files, key=lambda x: os.path.getctime(os.path.join(folder, x)))

    # variables that add adjustments to the single pictures to improve alignment
    stretch_images = [1, 2]
    x_offsets = [80, 0, 0, 0, 70, 0]

    y_offset = title_space

    # create draw object for the line between 3rd and 4th picture
    draw = ImageDraw.Draw(new_im)

    # paste the images below each other with transparent parts as black
    # create gallery
    for index, file in enumerate(image_files):
        im = Image.open(os.path.join(folder, file))
        if index in stretch_images:
            im = im.resize((max_width, im.size[1]), resample=Image.BICUBIC)
        bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
        bg.paste(im, mask=im.split()[3])  # 3 is the alpha channel
        new_im.paste(bg, (x_offsets[index], y_offset))
        y_offset += bg.size[1]
        if index == 2:
            # Draw a white line between the 3rd and 4th pictures and add some space
            y_offset += 10
            draw.line((0, y_offset, max_width, y_offset), fill=(255, 255, 255, 255), width=1)
            y_offset += divider_space
    # write text on top of the image
    title_font = ImageFont.truetype("arial.ttf", 250)
    text = f"{who} in {year}"
    text_width, text_height = title_font.getsize(text)
    text_x = (max_width - text_width) / 2  # center the text horizontally
    text_y = (title_space - text_height) / 2  # center the text vertically

    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=title_font)
    # save the new image
    new_im.save(f'rewind_images/rewind_gallery_{"server" if server else "user"}.png')


async def convert_file_to_discord_url(file, channel):
    """
    Returns file as discord attachment url.

    file: attachment we want as url
    channel: channel in which the file is posted
    """

    # sends file as discord attachment message in a certain channel
    m = await channel.send(
        file=discord.File(file),
        allowed_mentions=discord.AllowedMentions.none(),
    )
    # extract url from the message object
    url = m.attachments[0].url

    return url


def get_previous_year():
    """
    Returns previous year
    """
    current_year = datetime.datetime.now().year
    previous_year = current_year - 1
    return previous_year


def get_hour_interval(hour):
    """
    Returns the interval of a given hour to the next hour in a readable form
    3 -> 3 AM - 4 AM

    hour: start hour of the interval
    """
    current_time = datetime.datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
    next_time = current_time + datetime.timedelta(hours=1)
    current_hour = current_time.strftime('%I %p')
    next_hour = next_time.strftime('%I %p')
    current_hour = current_hour.lstrip("0")
    next_hour = next_hour.lstrip("0")

    return f"{current_hour} - {next_hour}"


def get_days_in_year(year):
    """
    Returns the amount of days in a year

    year: year
    """
    if calendar.isleap(year):
        return 366
    else:
        return 365


def get_weekday_name(day):
    """
    Returns weekdays name based on the number 1-7

    day: day of the week (0-Monday 6-Sunday)
    """

    weekdays = [
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
        'Sunday'
    ]
    return weekdays[int(day)]


def days_in_month(month, year):
    """
    Returns how many days a certain month has

    month: month
    year: year
    """
    return calendar.monthrange(year, month)[1]


class rewindoview(discord.ui.View):
    """
    View for year rewind
    """
    current_page: int = 1
    sep: int = 1

    async def send(self, ctx):
        """
        Sends the updated embed to a channel.

        ctx: message context object
        """
        self.message = await ctx.send(view=self)
        await self.update_message(self.data[:self.sep])

    def create_embed(self, data, main_info):
        """
        Creates and returns embed with the respective data that we need for the page.

        data: list of dictionaries containing page data
        main_info: dictionary with "year" and who" as key
        """
        page_number = f"Page {self.current_page}/{int(len(self.data) / self.sep)}"
        embed_dict = data[0]
        title = embed_dict["title"]
        thumbnail = embed_dict["thumbnail"]
        description = f'{embed_dict["description"]}\n[Album]({self.gallery})'
        color = embed_dict["color"]
        url = embed_dict["url"]
        footer = embed_dict["footer"]
        if footer is None:
            footer = page_number
        else:
            footer += f"\n{page_number}"

        year = main_info["year"]
        who = main_info["who"]

        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )

        try:
            who_icon_avatar = who.avatar
        except:
            who_icon_avatar = who.icon
        embed.set_thumbnail(url=thumbnail)
        embed.set_image(url=url)
        embed.set_footer(text=footer if footer is not None else f"{who} in {year}", icon_url=who_icon_avatar)

        return embed

    async def update_message(self, data):
        """
        Edits the message with the newly created embed.

        data: fraction of data we need for the page
        """
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(data, self.main_info), view=self)

    def update_buttons(self):
        """
        Changes the styles of the button depending on the current page
        """
        if self.current_page == 1:
            self.first_page_button.disabled = True
            self.prev_button.disabled = True

            self.first_page_button.style = discord.ButtonStyle.gray
            self.prev_button.style = discord.ButtonStyle.gray
        elif (self.current_page == 1) or (int(len(self.data) / self.sep)) == 1:
            self.first_page_button.disabled = True
            self.prev_button.disabled = True
            self.first_page_button.style = discord.ButtonStyle.gray
            self.prev_button.style = discord.ButtonStyle.gray
        else:
            self.first_page_button.disabled = False
            self.prev_button.disabled = False
            self.first_page_button.style = discord.ButtonStyle.green
            self.prev_button.style = discord.ButtonStyle.primary

        if self.current_page == int(len(self.data) / self.sep):
            self.next_button.disabled = True
            self.last_page_button.disabled = True
            self.last_page_button.style = discord.ButtonStyle.gray
            self.next_button.style = discord.ButtonStyle.gray
        else:
            self.next_button.disabled = False
            self.last_page_button.disabled = False
            self.last_page_button.style = discord.ButtonStyle.green
            self.next_button.style = discord.ButtonStyle.primary

    def get_current_page_data(self):
        """
        Extracts the data by slicing it depending on what the current page is
        """
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        if self.current_page == 1:
            from_item = 0
            until_item = self.sep
        if self.current_page == int(len(self.data) / self.sep) + 1:
            from_item = self.current_page * self.sep - self.sep
            until_item = len(self.data)
        return self.data[from_item:until_item]

    @discord.ui.button(label="|<",
                       style=discord.ButtonStyle.green)
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            await interaction.response.defer()
            self.current_page = 1

            await self.update_message(self.get_current_page_data())

    @discord.ui.button(label="<",
                       style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            await interaction.response.defer()
            self.current_page -= 1
            await self.update_message(self.get_current_page_data())

    @discord.ui.button(label=">",
                       style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            await interaction.response.defer()
            self.current_page += 1
            await self.update_message(self.get_current_page_data())

    @discord.ui.button(label=">|",
                       style=discord.ButtonStyle.green)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author_id:
            await interaction.response.defer()
            self.current_page = int(len(self.data) / self.sep)
            await self.update_message(self.get_current_page_data())


class Rewind(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.command()
    async def rewind(self, ctx, arg1: Union[discord.Member, str] = None, arg2: Union[discord.Member, str] = None):
        """
        Displays a rewindish stlye of graphics and information of a user in a particular year (by default 2022)

        arg1, arg2: year or @member

        """
        member = None
        year = get_previous_year()

        # extract respective year and member argument(s) from ctx
        for arg in [arg1, arg2]:
            if arg is not None:
                if isinstance(arg, discord.Member):
                    member = arg
                elif isinstance(arg, str):
                    try:
                        year = int(arg)
                        if year > datetime.datetime.now().year or year + 2 < int(str(ctx.guild.created_at)[:4]):
                            raise ValueError
                    except:
                        embed = discord.Embed(
                            description="Enter a valid Year",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                        return

        if member is None:
            member = ctx.author
        member_id = member.id

        embed_list = []

        channel = self.bot.get_channel(1066582054503993364)

        db = sqlite3.connect("chat.db")

        ############################################
        # CALENDAR
        ############################################
        create_heatmap_calendar(db, member_id, year, False)

        yearly_user_msgs = yearlyUserMessages(db.cursor(), member_id,
                                              str(year))
        if yearly_user_msgs is None:
            embed = discord.Embed(description=f"No Messages in {year}", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        # create configuration to our load bar.
        loading_stage = 0
        loading_stages = 8
        message = await ctx.send(f'Loading... {":black_large_square:" * loading_stages}')

        loading_stage = await send_load_message(message, loading_stage, loading_stages)

        yearly_days = yearlyDaysWhereUserSentMessage(db.cursor(), member_id, str(year))
        year_amount_days = get_days_in_year(year)
        percentage_active_of_year = round(yearly_days / year_amount_days * 100,
                                          1)
        messages_per_day = round(yearly_user_msgs / year_amount_days, 1)
        year_rank = TopYearlyRank(db.cursor(), str(year), member_id)[0]

        yearly_user_msgs = yearlyUserMessages(db.cursor(), member_id,
                                              str(year))
        yearly_days = yearlyDaysWhereUserSentMessage(db.cursor(), member_id,
                                                     str(year))

        peak_date, peak_msgs = yearlyMessagesUserPeak(db.cursor(), member_id,
                                                      str(year))
        peak_month, peak_month_msgs = yearlyMessagesUserPeakMonth(
            db.cursor(), member_id, str(year))
        peak_month_index = peak_month[5:7]
        month_name = get_month_name(int(peak_month_index))
        peak_month_days = days_in_month(int(peak_month_index), year)

        heatmap_calendar = {}
        heatmap_calendar["title"] = f"{member.name} in {year}"
        heatmap_calendar["description"] = (
            f"Sent {abbreviate_number(yearly_user_msgs)} Messages in {year}\n"
            f"{year} Leaderboard: #{year_rank}\n"
            f"Texted on {yearly_days} out of {year_amount_days} ({percentage_active_of_year}%) Days\n"
            f"~{messages_per_day} Messages per Day\n"
            f"Day peak: {DbYYYformat(peak_date)} ({abbreviate_number(peak_msgs)} Messages)\n"
            f"Month peak: {month_name} ({abbreviate_number(peak_month_msgs)} Messages)"
        )
        heatmap_calendar["thumbnail"] = member.avatar
        heatmap_calendar["color"] = 0xff0000
        heatmap_calendar["url"] = await convert_file_to_discord_url("rewind_images/user/heatmap_calendar_year.png", channel)
        heatmap_calendar["footer"] = None

        embed_list.append(heatmap_calendar)
        loading_stage = await send_load_message(message, loading_stage, loading_stages)
        ############################################
        # MONTH CHART
        ############################################

        highest_count_month = create_chart_month(db, member_id, year, False)
        highest_count_month_name = get_month_name(highest_count_month)

        percentage_peak_month_msgs = f"{round(peak_month_msgs / yearly_user_msgs *100,1)}%"

        month_chart = {}
        month_chart["title"] = "Messages by Month"
        month_chart["description"] = (
            f"Your best month was {highest_count_month_name}\n"
            f"{highest_count_month_name} accounts for {percentage_peak_month_msgs} messages in {year}\n"
            f"You sent  {abbreviate_number(int(peak_month_msgs / peak_month_days))} Messages/Day during {highest_count_month_name}"
        )
        month_chart["thumbnail"] = None
        month_chart["color"] = 0xff0000
        month_chart["url"] = await convert_file_to_discord_url("rewind_images/user/chart_month.png", channel)
        month_chart["footer"] = None

        embed_list.append(month_chart)
        loading_stage = await send_load_message(message, loading_stage, loading_stages)
        ############################################
        # YEARS/MONTHS COMPARISON
        ############################################
        create_heatmap_years_months(db, member_id, year, False)

        year_rank = userYearMessagesRank(db.cursor(), member_id, str(year))

        heatmap_years_months = {}
        heatmap_years_months["title"] = "Year Comparison"
        heatmap_years_months["description"] = f"{year} was your #{year_rank} year"
        heatmap_years_months["thumbnail"] = None
        heatmap_years_months["color"] = 0xff0000
        heatmap_years_months["url"] = await convert_file_to_discord_url("rewind_images/user/heatmap_years_months.png", channel)
        heatmap_years_months["footer"] = None

        embed_list.append(heatmap_years_months)
        loading_stage = await send_load_message(message, loading_stage, loading_stages)
        ############################################
        # HOUR OF WEEKDAY
        ############################################
        top1_hour, top1_weekday, top_1_counts = create_heatmap_hour_of_weekday(
            db, member_id, year, False)
        top1_hour_weekday = calendar.day_name[top1_weekday]
        top1_weekday_hour_interval = get_hour_interval(top1_hour)

        heatmap_weekday_hour = {}
        heatmap_weekday_hour["title"] = "Messages by Hour of Week"
        heatmap_weekday_hour["description"] = f"Your most active hour in the week was on {top1_hour_weekday} between {top1_weekday_hour_interval}"
        heatmap_weekday_hour["thumbnail"] = None
        heatmap_weekday_hour["color"] = 0x1f0073
        heatmap_weekday_hour["url"] = await convert_file_to_discord_url("rewind_images/user/heatmap_weekday_hour.png", channel)
        heatmap_weekday_hour["footer"] = None

        embed_list.append(heatmap_weekday_hour)
        loading_stage = await send_load_message(message, loading_stage, loading_stages)
        ############################################
        # HOUR OF DAY
        ############################################
        top1_day_hour = create_heatmap_hour_of_day(db, member_id, year, False)
        top1_day_hour_interval = get_hour_interval(top1_day_hour)

        heatmap_daytime = {}
        heatmap_daytime["title"] = "Messages by Hour of the Day"
        heatmap_daytime["description"] = f"Your most active hour of the day was between {top1_day_hour_interval}"
        heatmap_daytime["thumbnail"] = None
        heatmap_daytime["color"] = 0x1f0073
        heatmap_daytime["url"] = await convert_file_to_discord_url("rewind_images/user/heatmap_daytime.png", channel)
        heatmap_daytime["footer"] = None

        embed_list.append(heatmap_daytime)
        loading_stage = await send_load_message(message, loading_stage, loading_stages)
        ############################################
        # WEEKDAY
        ############################################
        highest_count_weekday = create_chart_weekday(db, member_id, year, False)
        highest_count_weekday_name = get_weekday_name(highest_count_weekday)

        chart_weekday = {}
        chart_weekday["title"] = "Messages by Weekday"
        chart_weekday["description"] = f"Your best weekday was {highest_count_weekday_name}"
        chart_weekday["thumbnail"] = None
        chart_weekday["color"] = 0x1f0073
        chart_weekday["url"] = await convert_file_to_discord_url("rewind_images/user/chart_weekday.png", channel)
        chart_weekday["footer"] = None

        embed_list.append(chart_weekday)
        loading_stage = await send_load_message(message, loading_stage, loading_stages)

        create_rewind_gallery(member.name, year, False)
        gallery_url = await convert_file_to_discord_url("rewind_images/rewind_gallery_user.png", channel)
        loading_stage = await send_load_message(message, loading_stage, loading_stages)

        pagination_view = rewindoview(timeout=120)
        pagination_view.data = embed_list
        pagination_view.author_id = ctx.author.id
        pagination_view.main_info = {"year": year, "who": member}
        pagination_view.ctx = ctx
        pagination_view.gallery = gallery_url
        await pagination_view.send(ctx)

    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.command(aliases=['rewindserver'])
    async def rewinds(self, ctx, year=None):
        """
        Displays a rewindish style of graphics and information of server in a particular year (by default previous year)

        year: year
        """
        start = time.time()
        if year is None:
            year = get_previous_year()
        else:
            try:
                year = int(year)
                if year > datetime.datetime.now().year or year + 2 < int(str(ctx.guild.created_at)[:4]):
                    raise ValueError
            except ValueError:
                embed = discord.Embed(description="Enter a valid Year",
                                      color=discord.Color.red())
                await ctx.send(embed=embed)
                return

        member_id = ctx.author.id

        channel = self.bot.get_channel(1066582054503993364)

        embed_list = []

        db = sqlite3.connect("chat.db")

        ############################################
        # CALENDAR
        ############################################
        create_heatmap_calendar(db, member_id, year, True)

        yearly_user_msgs, yearly_chars = yearlyServerMessages(db.cursor(), str(year))
        if yearly_user_msgs is None:
            embed = discord.Embed(description=f"No Messages in {year}", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        # await ctx.message.add_reaction("👍")

        # create configuration to our load bar.
        loading_stage = 0
        loading_stages = 8
        message = await ctx.send(f'Loading... {":black_large_square:" * loading_stages}')

        loading_stage = await send_load_message(message, loading_stage, loading_stages)

        yearly_days = dailyMessagesYearCounter(db.cursor(), str(year))
        year_amount_days = get_days_in_year(year)
        percentage_active_of_year = round(yearly_days / year_amount_days * 100, 1)

        unique_chatters = distinctChattersYear(db.cursor(), str(year))

        messages_per_day = round(yearly_user_msgs / year_amount_days, 1)

        peak_date, peak_msgs = yearlyMessagesPeak(db.cursor(), str(year))
        peak_month, peak_month_msgs = yearlyMessagesPeakMonth(db.cursor(), str(year))
        peak_month_index = peak_month[5:7]
        month_name = get_month_name(int(peak_month_index))
        peak_month_days = days_in_month(int(peak_month_index), year)

        heatmap_calendar = {}
        heatmap_calendar["title"] = f"{ctx.guild.name} in {year}"
        heatmap_calendar["description"] = (
            f"{abbreviate_number(yearly_user_msgs)} Messages were sent by {unique_chatters} unique members.\n"
            f"Members chatted on {yearly_days} out of {year_amount_days} ({percentage_active_of_year}%) Days\n"
            f"~{messages_per_day} Messages per Day\n"
            f"Day peak: {DbYYYformat(peak_date)} ({abbreviate_number(peak_msgs)} Messages)\n"
            f"Month peak: {month_name} ({abbreviate_number(peak_month_msgs)} Messages)"
        )
        heatmap_calendar["thumbnail"] = ctx.guild.icon
        heatmap_calendar["color"] = 0xff0000
        heatmap_calendar["url"] = await convert_file_to_discord_url("rewind_images/server/heatmap_calendar_year.png", channel)
        heatmap_calendar["footer"] = None

        embed_list.append(heatmap_calendar)
        loading_stage = await send_load_message(message, loading_stage, loading_stages)

        ############################################
        # MONTH CHART
        ############################################

        highest_count_month = create_chart_month(db, member_id, year, True)
        highest_count_month_name = get_month_name(highest_count_month)
        percentage_peak_month_msgs = f"{round(peak_month_msgs / yearly_user_msgs *100,1)}%"

        month_chart = {}
        month_chart["title"] = "Messages by Month"
        month_chart["description"] = (
            f"{ctx.guild.name}'s best month was {highest_count_month_name}\n"
            f"{highest_count_month_name} accounts for {percentage_peak_month_msgs} messages in {year}\n"
            f"{abbreviate_number(int(peak_month_msgs / peak_month_days))} messages per day were sent during {highest_count_month_name}"
        )
        month_chart["thumbnail"] = None
        month_chart["color"] = 0xff0000
        month_chart["url"] = await convert_file_to_discord_url("rewind_images/server/chart_month.png", channel)
        month_chart["footer"] = None

        embed_list.append(month_chart)
        loading_stage = await send_load_message(message, loading_stage, loading_stages)

        ############################################
        # YEARS/MONTHS COMPARISON
        ############################################

        create_heatmap_years_months(db, member_id, year, True)

        year_rank = YearServerMessagesRank(db.cursor(), str(year))

        embed = discord.Embed(description=f"{year} was {ctx.guild.name}'s  #{year_rank} year")
        # Set the image URL
        embed.set_image(url="attachment://heatmap_years_months.png")

        heatmap_years_months = {}
        heatmap_years_months["title"] = "Year Comparison"
        heatmap_years_months["description"] = f"{year} was {ctx.guild.name}'s  #{year_rank} year"
        heatmap_years_months["thumbnail"] = None
        heatmap_years_months["color"] = 0xff0000
        heatmap_years_months["url"] = await convert_file_to_discord_url("rewind_images/server/heatmap_years_months.png", channel)
        heatmap_years_months["footer"] = None

        embed_list.append(heatmap_years_months)
        loading_stage = await send_load_message(message, loading_stage, loading_stages)

        ############################################
        # HOUR OF WEEKDAY
        ############################################
        top1_hour, top1_weekday, top_1_counts = create_heatmap_hour_of_weekday(
            db, member_id, year, True)
        top1_hour_weekday = calendar.day_name[top1_weekday]
        top1_weekday_hour_interval = get_hour_interval(top1_hour)

        heatmap_weekday_hour = {}
        heatmap_weekday_hour["title"] = "Messages by Hour of Week"
        heatmap_weekday_hour["description"] = f"Most active hour of the week: {top1_hour_weekday} between {top1_weekday_hour_interval}"
        heatmap_weekday_hour["thumbnail"] = None
        heatmap_weekday_hour["color"] = 0xff0000
        heatmap_weekday_hour["url"] = await convert_file_to_discord_url("rewind_images/server/heatmap_weekday_hour.png", channel)
        heatmap_weekday_hour["footer"] = None

        embed_list.append(heatmap_weekday_hour)
        loading_stage = await send_load_message(message, loading_stage, loading_stages)

        ############################################
        # HOUR OF DAY
        ############################################
        top1_day_hour = create_heatmap_hour_of_day(db, member_id, year, True)
        top1_day_hour_interval = get_hour_interval(top1_day_hour)

        heatmap_daytime = {}
        heatmap_daytime["title"] = "Messages by Hour of the Day"
        heatmap_daytime["description"] = f"Most active hour of the day: {top1_day_hour_interval}"
        heatmap_daytime["thumbnail"] = None
        heatmap_daytime["color"] = 0xff0000
        heatmap_daytime["url"] = await convert_file_to_discord_url("rewind_images/server/heatmap_daytime.png", channel)
        heatmap_daytime["footer"] = None

        embed_list.append(heatmap_daytime)
        loading_stage = await send_load_message(message, loading_stage, loading_stages)

        ############################################
        # WEEKDAY
        ############################################
        highest_count_weekday = create_chart_weekday(db, member_id, year, True)
        highest_count_weekday_name = get_weekday_name(highest_count_weekday)

        chart_weekday = {}
        chart_weekday["title"] = "Messages by Weekday"
        chart_weekday["description"] = f"{ctx.guild.name}'s best weekday: {highest_count_weekday_name}"
        chart_weekday["thumbnail"] = None
        chart_weekday["color"] = 0xff0000
        chart_weekday["url"] = await convert_file_to_discord_url("rewind_images/server/chart_weekday.png", channel)
        chart_weekday["footer"] = None

        embed_list.append(chart_weekday)
        loading_stage = await send_load_message(message, loading_stage, loading_stages)

        create_rewind_gallery(ctx.guild.name, year, True)
        gallery_url = await convert_file_to_discord_url("rewind_images/rewind_gallery_server.png", channel)

        loading_stage = await send_load_message(message, loading_stage, loading_stages)

        pagination_view = rewindoview(timeout=120)
        pagination_view.data = embed_list
        pagination_view.author_id = ctx.author.id
        pagination_view.main_info = {"year": year, "who": ctx.guild}
        pagination_view.ctx = ctx
        pagination_view.gallery = gallery_url
        await pagination_view.send(ctx)
        end = time.time()
        print(f'Time taken: {end - start} seconds')

    @commands.command()
    async def test(self, ctx):
        pass


async def setup(bot):
    await bot.add_cog(Rewind(bot))
