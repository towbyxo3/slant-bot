import discord

from io import BytesIO
from utils import default
from discord.ext.commands.context import Context
from discord.ext.commands._types import BotT
from discord.ext import commands
import sys
import sqlite3
from queries.userchatqueries import get_user_rank_top_chatters_alltime
from helpers.numberformatting import abbreviate_number

sys.path.append("queries")
sys.path.append("helpers")


class ServerinfoView(discord.ui.View):
    """
    View to display the server info,
    with the options to show the server icon and server banner.
    """
    # whether the the history button has been used yet
    icon_button_trigger = False
    banner_button_trigger = False

    async def send(self, ctx):
        """
        Send the view to a channel. It creates a message
        containing the view and updates it.
        """
        self.message = await ctx.send(view=self)
        await self.update_message()

    def create_embed(self):
        """
        Creates the embed with the respective avatar
        (global or server depending on current page/previously pressed button).
        """
        """ Check info about current server """

        guild = self.ctx.guild
        ctx = self.ctx

        # overview of embed field name - value pairs.
        field_data = [
            ("Owner", guild.owner),
            ("Members", guild.member_count),
            ("Roles", len(guild.roles)),
            ("Text Channels", len(guild.text_channels)),
            ("Voice Channels", len(guild.voice_channels)),
            ("Boosts", guild.premium_subscription_count),
            ("Created", default.date(guild.created_at, ago=True))
        ]

        # construct embed
        embed = discord.Embed(
            description="Best Server on Discord!",
            timestamp=ctx.message.created_at,
            color=ctx.guild.me.color
        )
        embed.set_author(name=guild.name, icon_url=guild.banner)
        embed.set_thumbnail(url=guild.icon)

        # add fields
        for name, value in field_data:
            embed.add_field(name=name, value=value)

        embed.set_footer(icon_url=ctx.author.display_avatar, text=f"Server ID: {guild.id}")

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
        Updates the state of the buttons based on the current page.
        """
        # history button is disabled after its triggered to avoid spam
        if self.icon_button_trigger is True:
            self.icon.disabled = True
            self.icon.style = discord.ButtonStyle.gray
        elif not self.ctx.guild.icon:
            self.icon.label = "No Icon"
            self.icon.disabled = True
            self.icon.style = discord.ButtonStyle.gray

        if self.banner_button_trigger is True:
            self.banner.disabled = True
            self.banner.style = discord.ButtonStyle.gray
        elif not self.ctx.guild.banner:
            self.banner.label = "No Banner"
            self.banner.disabled = True
            self.banner.style = discord.ButtonStyle.gray

    @discord.ui.button(label="Icon", style=discord.ButtonStyle.primary)
    async def icon(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Get the current server icon """
        await interaction.response.defer()
        self.icon_button_trigger = True
        await self.update_message()
        ctx = self.ctx

        embed = discord.Embed(title="Server Icon")
        embed.set_image(url=ctx.guild.icon)
        await ctx.send(embed=embed)

    @discord.ui.button(label="Banner", style=discord.ButtonStyle.primary)
    async def banner(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ Get the current banner image """
        await interaction.response.defer()
        self.banner_button_trigger = True
        await self.update_message()
        ctx = self.ctx

        embed = discord.Embed(title="Server Banner")
        embed.set_image(url=ctx.guild.banner)
        await ctx.send(embed=embed)


class Discord_Info(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()

    @commands.command(aliases=['si', 'serverinfo'])
    async def server(self, ctx: Context[BotT]):
        """ Check info about current server """
        pagination_view = ServerinfoView(timeout=120)
        pagination_view.member = ctx.author
        pagination_view.ctx = ctx
        await pagination_view.send(ctx)

    @commands.command(aliases=['userinfo', 'ui'])
    async def user(self, ctx: Context[BotT], *, member: discord.Member = None):
        """ Get member information """
        member = member or ctx.author
        all_status = {
            "online": "🟢",
            "idle": "🟡",
            "dnd": "🔴",
            "offline": "⚫"
        }
        show_roles = "None"
        if len(member.roles) > 1:
            show_roles = ", ".join([
                f"<@&{x.id}>" for x in sorted(
                    member.roles,
                    key=lambda x: x.position,
                    reverse=True
                )
                if x.id != ctx.guild.default_role.id
            ])

        embed = discord.Embed(colour=member.top_role.colour.value)
        # embed.set_author(icon_url=member.display_avatar, name=f"{member.display_name}")
        embed.set_author(icon_url=member.avatar, name=f"{member.display_name}")
        embed.set_thumbnail(url=member.display_avatar)
        embed.add_field(name="@", value=f"<@{member.id}>")

        try:
            c_DB = sqlite3.connect("chat.db")
            c_cursor = c_DB.cursor()
            user_rank, id, user_msgs = get_user_rank_top_chatters_alltime(c_cursor, member.id)
            embed.add_field(name="Messages", value=f"{abbreviate_number(user_msgs)} (#{user_rank})")
        except Exception as e:
            print(e)
        embed.add_field(name="Registered", value=default.date(member.created_at), inline=False)
        embed.add_field(name="Joined", value=default.date(member.joined_at))
        embed.add_field(name=f"Roles ({len(member.roles)-1})", value=show_roles, inline=False)
        embed.set_footer(text=f"{all_status[str(member.status)]}: {member} · {member.id}")

        await ctx.send(embed=embed)

    @commands.command()
    async def names(self, ctx, member: discord.Member = None):
        """
        Get a member's history of names.
        """
        if member is None:
            member = ctx.author
        user = member.id
        m_DB = sqlite3.connect("messages.db")
        m_cursor = m_DB.cursor()

        m_cursor.execute("""
            SELECT name
            FROM namehistory
            WHERE Id = ?
            """, (user,))

        message = f"<@{user}> name history: \n"
        names = m_cursor.fetchall()
        result = ', '.join([item[0] for item in names])
        message += result

        await ctx.send(message)

    @commands.command(aliases=["bn"])
    async def banner(self, ctx, member: discord.Member = None):
        """
        Shows users global banner
        """
        if member is None:
            member = ctx.author

        user = await self.bot.fetch_user(member.id)

        if user.banner is None:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description="No global banner found."
                )
            )
        else:
            embed = discord.Embed()
            embed.set_author(
                name=user.name + "#" + user.discriminator,
                icon_url=user.avatar
            )
            embed.set_image(url=user.banner.url)

            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Discord_Info(bot))
