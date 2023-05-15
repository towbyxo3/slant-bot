import discord
import psutil
import os
from discord.ext import commands
from utils import default
import sys
from helpers.dateformatting import format_YMD_to_DMY

sys.path.append("helpers")


class AgeView(discord.ui.View):
    """
    View that displays a leaderboard of the server members based on their
    - registration date
    - join date in a server
    It provides buttons for sorting the leaderboard by oldest and youngest
    and toggling between the 2 base criteria (registration or join date).
    """

    # representing the current page of the leaderboard
    # page 1 for registration date
    # page 2 for join date
    current_page: int = 1
    # sort_by_youngest = False -> Sort by oldest
    # sort_by_youngest = True -> Sort by youngest
    sort_by_youngest = False

    async def send(self, ctx):
        """
        Send the view to a channel. It creates a message
        containing the view and updates it.
        """
        self.message = await ctx.send(view=self)
        await self.update_message()

    def create_embed(self):
        """
        Gathers the leaderboard data based on pressed buttons and creates embed.
        """
        if self.current_page == 1:
            true_member_count = len([m for m in self.ctx.guild.members if not m.bot])
            member_list = {}
            guild = self.ctx.guild
            for member in guild.members:
                if not member.bot:
                    member_name = member.id
                    member_register = str(member.created_at)[:16]
                    member_list[member_name] = member_register
            sorted_list = sorted(member_list.items(), key=lambda x: x[1], reverse=self.sort_by_youngest)

            embed = discord.Embed(
                title=f"{'Youngest' if self.sort_by_youngest else 'Oldest'} Discord Users in {guild.name}",
                timestamp=self.ctx.message.created_at,
                color=discord.Color.red()
            )
            embed.set_author(
                name=f"{guild.name} Leaderboard",
                icon_url=guild.icon
            )
            embed.set_thumbnail(url=guild.icon)

            leaderboard_text = ""

            for rank, data in enumerate(sorted_list[:self.num], 1):
                date = format_YMD_to_DMY(data[1][:10])
                user = f"<@{data[0]}>"
                leaderboard_text += f"`{rank}.` | {user} {date}\n"

            embed.add_field(
                name="Rank | Member | Created on",
                value=leaderboard_text,
                inline=False
            )
            embed.set_footer(text=f"{rank} out of {true_member_count} Members")
        elif self.current_page == 2:
            true_member_count = len([m for m in self.ctx.guild.members if not m.bot])
            member_list = {}
            guild = self.ctx.guild
            for member in guild.members:
                if not member.bot:
                    member_name = member.id
                    member_register = str(member.joined_at)[:16]
                    member_list[member_name] = member_register
            sorted_list = sorted(member_list.items(), key=lambda x: x[1], reverse=self.sort_by_youngest)

            embed = discord.Embed(
                title=f"{'Youngest' if self.sort_by_youngest else 'Oldest'} {guild.name} Members",
                timestamp=self.ctx.message.created_at,
                color=discord.Color.red()
            )
            embed.set_author(
                name=f"{guild.name} Leaderboard",
                icon_url=guild.icon
            )
            embed.set_thumbnail(url=guild.icon)

            leaderboard_text = ""
            for rank, data in enumerate(sorted_list[:self.num], 1):
                date = format_YMD_to_DMY(data[1][:10])
                user = f"<@{data[0]}>"
                leaderboard_text += f"`{rank}.` | {user} {date}\n"

            embed.add_field(
                name="Rank | Member | Joined on",
                value=leaderboard_text,
                inline=False
            )
            embed.set_footer(text=f"{rank} out of {true_member_count} Members")

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
        page 1 - leaderboard sorted by registration date
        page 2 - leaderboard sorted by join date
        """
        if self.current_page == 1:
            self.registration.disabled = True
            self.join.disabled = False
            self.registration.style = discord.ButtonStyle.gray
            self.join.style = discord.ButtonStyle.green

        if self.current_page == 2:
            self.registration.disabled = False
            self.join.disabled = True
            self.registration.style = discord.ButtonStyle.green
            self.join.style = discord.ButtonStyle.gray

        self.reverse.label = "Oldest" if self.sort_by_youngest else "Youngest"

    @discord.ui.button(label="Registration Date", style=discord.ButtonStyle.green)
    async def registration(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Returns the oldest discord users of the server.
        """
        self.current_page = 1
        await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(label="Join Date", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Returns the oldest members of the server.
        """
        self.current_page = 2
        await self.update_message()
        await interaction.response.defer()

    @discord.ui.button(label="Youngest", style=discord.ButtonStyle.blurple)
    async def reverse(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Toggles sort order.
        """
        self.sort_by_youngest = not self.sort_by_youngest
        await self.update_message()
        await interaction.response.defer()


class AgeLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command(alises=["oldest", "ageleaderboard", "agelb"])
    async def age(self, ctx, num=10):
        """
        Oldest or youngest members in Server by
        - Discord Registration Date
        - Server Join Date
        .
        """
        pagination_view = AgeView(timeout=120)
        pagination_view.num = num
        pagination_view.ctx = ctx
        await pagination_view.send(ctx)


async def setup(bot):
    await bot.add_cog(AgeLeaderboard(bot))
