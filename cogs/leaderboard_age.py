import discord
import psutil
import os
from discord.ext import commands
from utils import default
import sys
from helpers.dateformatting import DbYYYformat

sys.path.append("helpers")


class Age(discord.ui.View):
    def __init__(self, ctx, num):
        super().__init__()
        self.ctx = ctx
        self.num = num

    @discord.ui.button(label="Registration Date", style=discord.ButtonStyle.blurple)
    async def Registration(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Returns the oldest discord users of the server.
        """

        true_member_count = len([m for m in self.ctx.guild.members if not m.bot])
        member_list = {}
        guild = self.ctx.guild
        for member in guild.members:
            if not member.bot:
                member_name = member.id
                member_register = str(member.created_at)[:16]
                member_list[member_name] = member_register
        sorted_list = sorted(member_list.items(), key=lambda x: x[1])

        embed = discord.Embed(
            title=f"Oldest Discord Users in {guild.name}",
            timestamp=self.ctx.message.created_at,
            color=discord.Color.red()
        )
        embed.set_author(
            name=f"{guild.name} Leaderboard",
            icon_url=guild.icon
        )
        embed.set_thumbnail(url=guild.icon)

        leaderboard_text = ""
        rank = 1
        for data in sorted_list[:self.num]:
            date = DbYYYformat(data[1][:10])
            user = f"<@{data[0]}>"
            leaderboard_text += f"`{rank}.` | {user} {date}\n"
            rank += 1

        embed.add_field(
            name="Rank | Member | Created on",
            value=leaderboard_text,
            inline=False
        )
        embed.set_footer(text=f"{rank-1} out of {true_member_count} Members")

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()

    @discord.ui.button(label="Join Date", style=discord.ButtonStyle.blurple)
    async def Join(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Returns the oldest members of the server.
        """

        true_member_count = len([m for m in self.ctx.guild.members if not m.bot])
        member_list = {}
        guild = self.ctx.guild
        for member in guild.members:
            if not member.bot:
                member_name = member.id
                member_register = str(member.joined_at)[:16]
                member_list[member_name] = member_register
        sorted_list = sorted(member_list.items(), key=lambda x: x[1])

        embed = discord.Embed(
            title=f"Oldest {guild.name} Members",
            timestamp=self.ctx.message.created_at,
            color=discord.Color.red()
        )
        embed.set_author(
            name=f"{guild.name} Leaderboard",
            icon_url=guild.icon
        )
        embed.set_thumbnail(url=guild.icon)

        leaderboard_text = ""
        rank = 1
        for data in sorted_list[:self.num]:
            date = DbYYYformat(data[1][:10])
            user = f"<@{data[0]}>"
            leaderboard_text += f"`{rank}.` | {user} {date}\n"
            rank += 1

        embed.add_field(
            name="Rank | Member | Joined on",
            value=leaderboard_text,
            inline=False
        )
        embed.set_footer(text=f"{rank-1} out of {true_member_count} Members")

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()


class AgeLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command()
    async def age(self, ctx, num=10):
        """
        Oldest Users in Server by Registration Date and Server Join Date
        """

        true_member_count = len([m for m in ctx.guild.members if not m.bot])

        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at,
            title="Select Age Criteria",
            description=f"Oldest {ctx.guild.name} Members by Registration Date or Join Date"
        )
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.set_footer(
            text=f"Server ID: {ctx.guild.id} | {true_member_count} Members"
        )

        await ctx.send(embed=embed, view=Age(ctx, num))


async def setup(bot):
    await bot.add_cog(AgeLeaderboard(bot))
