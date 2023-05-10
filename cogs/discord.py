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


class Discord_Info(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()

    @commands.command()
    @commands.guild_only()
    async def roles(self, ctx: Context[BotT]):
        """ Get all roles in current server """
        allroles = ""

        for num, role in enumerate(sorted(ctx.guild.roles, reverse=True), start=1):
            allroles += f"[{str(num).zfill(2)}] {role.id}\t{role.name}\t[ Users: {len(role.members)} ]\r\n"

        data = BytesIO(allroles.encode("utf-8"))
        await ctx.send(content=f"Roles in **{ctx.guild.name}**", file=discord.File(data, filename=f"{default.timetext('Roles')}"))

    @commands.command(aliases=["joindate", "joined"])
    @commands.guild_only()
    async def joinedat(self, ctx: Context[BotT], *, user: discord.Member = None):
        """ Check when a user joined the current server """
        user = user or ctx.author
        await ctx.send("\n".join([
            f"**{user}** joined **{ctx.guild.name}**",
            f"{default.date(user.joined_at, ago=True)}"
        ]))

    @commands.command()
    @commands.guild_only()
    async def mods(self, ctx: Context[BotT]):
        """ Check which mods are online on current guild """
        message = ""
        all_status = {
            "online": {"users": [], "emoji": "🟢"},
            "idle": {"users": [], "emoji": "🟡"},
            "dnd": {"users": [], "emoji": "🔴"},
            "offline": {"users": [], "emoji": "⚫"}
        }

        for user in ctx.guild.members:
            user_perm = ctx.channel.permissions_for(user)
            if user_perm.kick_members or user_perm.ban_members:
                if not user.bot:
                    all_status[str(user.status)]["users"].append(f"**{user}**")

        for g in all_status:
            if all_status[g]["users"]:
                message += f"{all_status[g]['emoji']} {', '.join(all_status[g]['users'])}\n"

        await ctx.send(f"Mods in **{ctx.guild.name}**\n{message}")

    @commands.group(aliases=['si', 'serverinfo'])
    @commands.guild_only()
    async def server(self, ctx: Context[BotT]):
        """ Check info about current server """

        guild = ctx.guild

        embed = discord.Embed(description="Best server on Discord!",
                              timestamp=ctx.message.created_at,
                              color=discord.Color.blue())
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.banner)
        embed.set_thumbnail(url=ctx.guild.icon)
        embed.add_field(name="Owner", value=guild.owner)
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Roles", value=len(guild.roles))
        embed.add_field(name="Text Channels", value=len(guild.text_channels))
        embed.add_field(name="Voice Channels", value=len(ctx.guild.voice_channels))
        embed.add_field(name="Boosts", value=guild.premium_subscription_count)
        embed.add_field(name="Created", value=default.date(ctx.guild.created_at, ago=True))
        embed.set_footer(icon_url=ctx.author.avatar, text="Server ID: " + str(guild.id))
        await ctx.send(embed=embed)

    @server.command(name="avatar", aliases=["icon"])
    @commands.guild_only()
    async def server_avatar(self, ctx: Context[BotT]):
        """ Get the current server icon """
        if not ctx.guild.icon:
            return await ctx.send("This server does not have an icon...")

        format_list = []
        formats = ["JPEG", "PNG", "WebP"]
        if ctx.guild.icon.is_animated():
            formats.append("GIF")

        for img_format in formats:
            format_list.append(
                f"[{img_format}]({ctx.guild.icon.replace(format=img_format.lower(), size=1024)})")

        embed = discord.Embed()
        embed.set_image(url=f"{ctx.guild.icon.with_size(256).with_static_format('png')}")
        embed.title = "Icon formats"
        embed.description = " **-** ".join(format_list)

        await ctx.send(f"🖼 Icon to **{ctx.guild.name}**", embed=embed)

    @server.command(name="banner")
    async def server_banner(self, ctx: Context[BotT]):
        """ Get the current banner image """
        if not ctx.guild.banner:
            return await ctx.send("This server does not have a banner...")

        await ctx.send("\n".join([
            f"Banner of **{ctx.guild.name}**",
            f"{ctx.guild.banner.with_format('png')}"
        ]))

    @commands.command(aliases=['userinfo', 'ui'])
    @commands.guild_only()
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
        except:
            pass
        embed.add_field(name="Registered", value=default.date(member.created_at), inline=False)
        embed.add_field(name="Joined B40", value=default.date(member.joined_at))
        embed.add_field(name=f"Roles ({len(member.roles)-1})", value=show_roles, inline=False)
        embed.set_footer(text=f"{all_status[str(member.status)]}: {member} · {member.id}")

        await ctx.send(embed=embed)

    @commands.command()
    async def names(self, ctx, member: discord.Member = None):
        """
        Gets history of names of user.
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
