import sqlite3
import discord
import psutil
import os
import sys
from discord.ext import commands
from utils import default
from queries.userchatqueries import *
from queries.serverchatqueries import *
from helpers.dateformatting import *
from helpers.numberformatting import *

sys.path.append("queries")
sys.path.append("helpers")

"""
def get_last_week(year, week):
    # Create a datetime object for the given year and week
    dt = datetime.datetime.strptime(f'{year}-W{week}-1', '%Y-W%W-%w')

    # Subtract one week from the datetime object
    last_week = dt - datetime.timedelta(weeks=1)

    # Return the year and week number of the previous week
    return last_week.year, last_week.strftime('%U')

prev_year, prev_week = get_last_week(year, week)

prev_user_rank = get_user_rank_top_chatters_week(c_cursor, str(prev_year), (prev_week), id)[0]

rank_diff = prev_user_rank-rank
change_symbol = '🟩' if rank_diff > 0 else '🟥' if rank_diff < 0 else '⬛'
change = '+' + str(rank_diff) if rank_diff > 0 else str(rank_diff) if rank_diff < 0 else '-0'
"""


def create_top10_text(lb_data, server_msgs):
    """
    Creates the top ten text representation and
    calculates the total number of messages sent by the top chatters.

    lb_data (list): A list of tuples representing the leaderboard data.
                    (id, msgs a member sent)
    server_msgs (int): The total number of server msgs in a time period.
    """
    top_10_total_msgs = 0
    topten_text = ""
    for rank, (id, msgs) in enumerate(lb_data, start=1):
        top_10_total_msgs += msgs
        topten_text += f"`{rank}.` <@{id}> **{abbreviate_number(msgs)}** Msgs | {round(msgs*100/server_msgs, 1)}%\n"

    return topten_text, top_10_total_msgs


class ChatLeaderboardView(discord.ui.View):
    """
    View that displays a server's chat leaderboard with a focus on
    user messages. It retrieves and organizes chat activity statistics
    on the server and then creates an embed with the information, including
    rankings, percentages, and server-wide metrics, for different time periods.
    """
    # page 1 - weekly chat leaderboard
    # page 2 - monthly chat leaderboard
    # page 3 - yearly chat leaderboard
    # page 4 - alltime chat leaderboard
    WEEKLY = 1
    MONTHLY = 2
    YEARLY = 3
    ALLTIME = 4

    # representing the current page of the leaderboard
    current_page: int = 1

    async def send(self, ctx):
        """
        Send the view to a channel. It creates a message
        containing the view and updates it.
        """
        self.message = await ctx.send(view=self)
        await self.update_message()

    def create_embed(self):
        """
        It retrieves various statistics related to server chat activity
        on server, such as top chatters, message counts, and
        server-wide metrics.
        It then constructs an embed to display this information, including
        rankings, percentages, and server statistics, for different time periods
        - weekly (page 1)
        - monthly (page 2)
        - yearly (page 3)
        - all time (page 4)
        based on the current page.
        """

        # connect to database
        user = self.member.id
        ctx = self.ctx
        c_DB = sqlite3.connect("chat.db")
        c_cursor = c_DB.cursor()

        # 1 - weekly, 2 - monthly, 3 - yearly, 4 - alltime
        if self.current_page == self.WEEKLY:
            year, month, week = get_todays_date()
            first_day, last_day = get_week_dates(year, week)

            unique_chatters = get_distinct_chatters_count_week(c_cursor, year, week)
            user_rank, id, user_msgs = get_user_rank_top_chatters_week(c_cursor, year, week, user)
            server_msgs, server_chars = get_weekly_server_msgs(c_cursor, year, week)

            author_text = f"WEEK {week} | {first_day} - {last_day}"

            topten_text, top_10_total_msgs = create_top10_text(top_chatters_week(c_cursor, year, week), server_msgs)

        if self.current_page == self.MONTHLY:
            year, month, week = get_todays_date_actually()
            month_name = get_month_name(month)

            unique_chatters = get_distinct_chatters_count_month(c_cursor, year, month)
            user_rank, id, user_msgs = get_user_rank_top_chatters_month(c_cursor, year, month, user)
            server_msgs, server_chars = get_monthly_server_msgs(c_cursor, year, month)

            author_text = f"{month_name} {str(year)}"
            topten_text, top_10_total_msgs = create_top10_text(top_chatters_month(c_cursor, year, month), server_msgs)

        if self.current_page == self.YEARLY:
            year, month, week = get_todays_date_actually()

            unique_chatters = get_distinct_chatters_count_year(c_cursor, year)
            user_rank, id, user_msgs = get_user_rank_top_chatters_year(c_cursor, year, user)
            server_msgs, server_chars = get_yearly_server_msgs(c_cursor, year)

            author_text = year
            topten_text, top_10_total_msgs = create_top10_text(top_chatters_year(c_cursor, year), server_msgs)

        if self.current_page == self.ALLTIME:
            unique_chatters = get_distinct_chatters_count_alltime(c_cursor)
            user_rank, id, user_msgs = get_user_rank_top_chatters_alltime(c_cursor, user)
            server_msgs, server_chars = get_alltime_server_msgs(c_cursor)

            author_text = "All-Time"
            topten_text, top_10_total_msgs = create_top10_text(top_chatters_alltime(c_cursor), server_msgs)

        # embed construction
        embed = discord.Embed(color=self.member.color)
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_author(
            name=author_text,
            icon_url=self.ctx.guild.icon
        )

        time_frame = ["weekly", "monthly", "yearly", "all"]
        time_text = time_frame[self.current_page - 1]

        topten_text += f"\n**TOP 10 sent  {round(top_10_total_msgs*100/server_msgs, 1)}% of {time_text} server messages**"

        embed.add_field(
            name=f"Rank | Msgs | % of {time_text} server msgs",
            value=topten_text, inline=False
        )
        embed.add_field(
            name=f"Server: {unique_chatters} Unique Chatters",
            value=f"""
                **{abbreviate_number(server_msgs)}** Messages | {abbreviate_number(server_chars)} Chars | {int(server_chars/server_msgs)} Chars/Msg
                    """
        )
        embed.set_footer(
            icon_url=self.member.avatar,
            text=f"""
                {user_rank}. {self.member.name}#{self.member.discriminator} | {abbreviate_number(user_msgs)} Msgs | {round(user_msgs*100/server_msgs, 1)}% of {time_text} server messages
                    """
        )

        return embed

    async def update_message(self):
        """
        Updates the message with the current state of the view.
        It updates the buttons and the embed.
        """
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(), view=self)

    def update_buttons(self):
        """
        Updates the state of the buttons based on the current page
        Current page button is grayed out and disabled.
        """
        self.weekly.style = discord.ButtonStyle.blurple
        self.monthly.style = discord.ButtonStyle.blurple
        self.yearly.style = discord.ButtonStyle.blurple
        self.alltime.style = discord.ButtonStyle.blurple

        self.weekly.disabled = False
        self.monthly.disabled = False
        self.yearly.disabled = False
        self.alltime.disabled = False

        if self.current_page == self.WEEKLY:
            self.weekly.disabled = True
            self.weekly.style = discord.ButtonStyle.gray

        if self.current_page == self.MONTHLY:
            self.monthly.disabled = True
            self.monthly.style = discord.ButtonStyle.gray

        if self.current_page == self.YEARLY:
            self.yearly.disabled = True
            self.yearly.style = discord.ButtonStyle.gray

        if self.current_page == self.ALLTIME:
            self.alltime.disabled = True
            self.alltime.style = discord.ButtonStyle.gray

    @discord.ui.button(label="Weekly", style=discord.ButtonStyle.blurple)
    async def weekly(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 1
        await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(label="Monthly", style=discord.ButtonStyle.blurple)
    async def monthly(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 2
        await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(label="Yearly", style=discord.ButtonStyle.blurple)
    async def yearly(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 3
        await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(label="All-Time", style=discord.ButtonStyle.blurple)
    async def alltime(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 4
        await self.update_message()
        await interaction.response.defer()


class ChatLeaderboard(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command(aliases=['lb', 'topchatter', 'topchatters', 'msglb', 'chatlb', 'chatleaderboard', 'mostmsgs', 'mostmessages', 'messageleaderboard'])
    async def leaderboard(self, ctx, member: discord.Member = None):
        """
        Chat leaderboards of current periods
        """
        if member is None:
            member = ctx.author

        pagination_view = ChatLeaderboardView(timeout=120)
        pagination_view.member = member
        pagination_view.ctx = ctx
        await pagination_view.send(ctx)


async def setup(bot):
    await bot.add_cog(ChatLeaderboard(bot))
