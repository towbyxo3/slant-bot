import sqlite3
import discord
import psutil
import os
from discord import ui
import datetime
from typing import Union

from discord.ext import commands
from utils import default
import io
import sys
from queries.userchatqueries import *
from queries.serverchatqueries import *
from helpers.dateformatting import *
from helpers.numberformatting import *

sys.path.append("queries")
sys.path.append("helpers")


def entry_avatar(cursor, db, date, id, url, original_url):
    """
    Stores information of a users avatar in database.

    cursor: db.cursor()
    db: database in which the data is stored
    date: date of avatar entry
    id: member id
    url: url of the discord message attachment (permanently working)
    original_url: original discord avatar url (needed to identify unique avatars)
    """
    cursor.execute('''
        INSERT INTO avhistory (Date, Id, Url, OriginalUrl)
        VALUES (?, ?, ?, ?)
    ''', (date, id, url, original_url))
    db.commit()


# def getUserOfAvID(cursor, idAV):
#     cursor.execute("""
#         SELECT Id
#         FROM avhistory
#         WHERE idAV = ?
#         """, (idAV,))
#     user = cursor.fetchone()
#     return user[0] if user else None


def delete_avatar(cursor, db, idAV):
    """
    Deletes the database entry of a certain avatar.
    This function is available in the avatar history command where
    only the owner of the avatar has permission to delete the avatar.

    cursor: db.cursor()
    db: avatar history database
    idAV: unique identifier of an avatar within the database
    """
    cursor.execute("""
        DELETE FROM
        avhistory
        WHERE idAV = ?
        """, (idAV,))
    db.commit()


def delete_all_avatar(cursor, db, id, current_av):
    """
    Deletes all avatars of a user except the currently used one

    cursor: db.cursor()
    db: avatar history database
    id: member id
    current_av: currently used avatar of member
    """
    cursor.execute("""
        SELECT count(id)
        FROM avhistory
        WHERE ID = ?
        """, (id,))
    items = cursor.fetchall()
    items = items[0][0]
    cursor.execute("""
        DELETE FROM
        avhistory
        WHERE id = ? AND ORIGINALUrl != ?
        """, (id, current_av))
    db.commit()

    return items


def avh_create_table(cursor, db):
    """
    Creates the avatar history table if it doesn't exist yet
    """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS "avhistory"
        (
            "Date"  TEXT,
            "Id"    TEXT,
            "Url"   TEXT,
            "OriginalUrl"   TEXT,
            "idAV"  INTEGER,
            PRIMARY KEY("idAV" AUTOINCREMENT))
            ''')
    db.commit()


def url_not_in_DB(cursor, url):
    """
    Checks wheither a given url is in the database.
    This avoids duplicates.

    cursor: db.cursor()
    url: original avatar url
    """
    cursor.execute('''
        SELECT *
        FROM avhistory
        WHERE OriginalUrl=?
        ''', (url,))
    result = cursor.fetchone()

    # Return False if the url exists, False otherwise
    return result is None


def get_avatar_history(cursor, id):
    """
    Fetches all avatars of a user in the avatar history database

    cursor: db.execute()
    id: member id
    """
    cursor.execute("""
        SELECT Date, Id, Url, idAV
        FROM avhistory WHERE Id = ?
        ORDER BY Date DESC
        """, (id,))
    data = cursor.fetchall()

    return data


class AvatarView(discord.ui.View):
    """
    View for Global and Server avatars
    """

    def __init__(self, ctx, member):
        super().__init__()
        self.ctx = ctx
        self.member = member

    @discord.ui.button(label="Global", style=discord.ButtonStyle.gray)
    async def Global(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = self.member
        ctx = self.ctx

        embed = discord.Embed(
            colour=member.color,
            timestamp=ctx.message.created_at
        )
        embed.set_author(
            icon_url=member.avatar,
            name=f"{member}   •   {member.id}"
        )
        embed.set_image(url=member.avatar)
        # embed.set_footer(icon_url=ctx.guild.icon, text="Server ID: " + str(ctx.guild.id))

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()

    @discord.ui.button(label="Server", style=discord.ButtonStyle.blurple)
    async def Server(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = self.member
        ctx = self.ctx

        embed = discord.Embed(
            colour=member.color,
            timestamp=ctx.message.created_at
        )
        embed.set_author(
            icon_url=member.display_avatar,
            name=f"{member}   •   {member.id}"
        )
        embed.set_image(url=member.display_avatar)
        # embed.set_footer(icon_url=ctx.guild.icon, text="Server ID: " + str(ctx.guild.id))

        await interaction.message.edit(embed=embed)
        await interaction.response.defer()


class AvatarHistoryView(discord.ui.View):
    """
    View for avatar history ofa  member
    """
    current_page: int = 1
    sep: int = 1

    async def send(self, ctx):
        self.message = await ctx.send(view=self)
        await self.update_message(self.data[:self.sep])

    def create_embed(self, data):
        embed = discord.Embed(
            title=f"{self.current_page} / {int(len(self.data) / self.sep)}",
            color=discord.Color.blue()
        )

        for item in data:
            embed.set_author(
                name=f"{self.user.name} # {self.user.discriminator}",
                icon_url=self.user.avatar
            )
            embed.set_image(url=item['url'])
            embed.set_footer(
                # icon_url=member.avatar,
                text=(
                    f"Avatar ID: {item['idAV']} • {DbYYYformat(item['date'][:10])}"
                )
            )
        return embed

    async def update_message(self, data):
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(data), view=self)

    def update_buttons(self):
        if self.current_page == 1:
            self.first_page_button.disabled = True
            self.prev_button.disabled = True
            self.delete_button.disabled = True
            self.delete_button.style = discord.ButtonStyle.gray
            self.first_page_button.style = discord.ButtonStyle.gray
            self.prev_button.style = discord.ButtonStyle.gray
        elif (self.current_page == 1) or (int(len(self.data) / self.sep)) == 1:
            self.first_page_button.disabled = True
            self.prev_button.disabled = True
            self.delete_button.disabled = True
            self.delete_button.style = discord.ButtonStyle.gray
            self.first_page_button.style = discord.ButtonStyle.gray
            self.prev_button.style = discord.ButtonStyle.gray
        else:
            self.first_page_button.disabled = False
            self.prev_button.disabled = False
            self.delete_button.disabled = False
            self.delete_button.style = discord.ButtonStyle.red
            self.first_page_button.style = discord.ButtonStyle.green
            self.prev_button.style = discord.ButtonStyle.primary

        if self.current_page == int(len(self.data) / self.sep):
            self.next_button.disabled = True
            self.last_page_button.disabled = True
            # self.delete_button.disabled = False
            self.last_page_button.style = discord.ButtonStyle.gray
            self.next_button.style = discord.ButtonStyle.gray
        else:
            self.next_button.disabled = False
            self.last_page_button.disabled = False
            self.last_page_button.style = discord.ButtonStyle.green
            self.next_button.style = discord.ButtonStyle.primary

    def get_current_page_data(self):
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

    @discord.ui.button(label="DEL",
                       style=discord.ButtonStyle.red)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        first_entry = self.data[self.current_page - 1]
        id_value = first_entry['id']
        idAV = first_entry['idAV']

        if interaction.user.id == int(id_value):
            await interaction.response.defer()
            avh_DB = sqlite3.connect('avhistory.db')
            avh_cursor = avh_DB.cursor()

            delete_avatar(avh_cursor, avh_DB, idAV)
            avh_DB.close()
            self.data.pop(self.current_page - 1)

            embed = discord.Embed(
                description=f"Successfully deleted avatar (ID: {idAV})",
                color=discord.Color.green()
            )
            await self.ctx.send(embed=embed)
            self.current_page = self.current_page - 1
            await self.update_message(self.get_current_page_data())


class AvHistory(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if (before.avatar is None) and (after.avatar is None):
            return

        avh_DB = sqlite3.connect('avhistory.db')
        avh_cursor = avh_DB.cursor()
        avh_create_table(avh_cursor, avh_DB)

        # create a list of a members avatars
        avatars = [after.avatar, after.display_avatar, before.avatar, before.display_avatar]
        # get rid of none types and duplicates
        avatars = [x for x in avatars if x is not None]
        avatars = [x for x in avatars if url_not_in_DB(avh_cursor, str(x))]
        avatars = list(set(avatars))

        # check if we have to add avatars to the database
        if len(avatars) == 0:
            return

        now = str(datetime.datetime.now())

        # for every new and unique avatar, store bytes of the picture
        # send the picture as file in a seperate channel,
        # save the attachment url and store the gathered data in a database
        for av in avatars:
            try:
                file_name = f"{av.key}.{'gif' if av.is_animated() else 'png'}"
                file_bytes = await av.read()
                channel = self.bot.get_channel(1057132789935394908)
                text = f"{after}'s avatar (ID: {after.id})"
                member = channel.guild.get_member(after.id)
                if member:
                    text += f" {after.mention}"
                m = await channel.send(
                    file=discord.File(io.BytesIO(file_bytes), filename=file_name),
                    content=text,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                url = m.attachments[0].url
                entry_avatar(avh_cursor, avh_DB, now, after.id, url, str(av))
                print(url)
            except (discord.NotFound, discord.HTTPException, AttributeError):
                pass

    @commands.command(aliases=['av', 'pfp', 'avt', 'pf'])
    async def avatar(self, ctx, member: discord.Member = None):
        """
        Displays a members global (and if given, server avatar in a embed view)

        member: @member
        """
        if member is None:
            member = ctx.author

        embed = discord.Embed(
            colour=member.color,
            timestamp=ctx.message.created_at
        )
        embed.set_author(
            icon_url=member.avatar,
            name=f"{member}   •   {member.id}"
        )
        embed.set_image(url=member.display_avatar if member.avatar is None else member.avatar)
        # embed.set_footer(icon_url=ctx.guild.icon, text="Server ID: " + str(ctx.guild.id))

        if member.avatar == member.display_avatar or member.avatar is None:
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed, view=AvatarView(ctx, member))

    @commands.command(aliases=['avh', 'avhistory'])
    async def avatarhistory(self, ctx, member: Union[discord.Member, int, str] = None):
        """
        Displays a gallery of a members current and past avatars

        member: @member
        """
        if member is None:
            member = ctx.author

        # before we send the view, we check if the current display_avatar
        # and avatar are in the database, if not, add them

        try:
            avh_DB = sqlite3.connect('avhistory.db')
            avh_cursor = avh_DB.cursor()
            now = str(datetime.datetime.now())
            avatars = list(set([member.display_avatar, member.avatar]))

            for av in avatars:
                if url_not_in_DB(avh_cursor, str(av)):
                    file_name = f"{av.key}.{'gif' if av.is_animated() else 'png'}"
                    file_bytes = await av.read()
                    channel = self.bot.get_channel(1057132789935394908)
                    text = f"{member}'s avatar (ID: {member.id})"
                    member = channel.guild.get_member(member.id)
                    if member:
                        text += f" {member.mention}"
                    m = await channel.send(
                        file=discord.File(io.BytesIO(file_bytes), filename=file_name),
                        content=text,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                    url = m.attachments[0].url
                    entry_avatar(avh_cursor, avh_DB, now, member.id, url, str(av))
        except (discord.NotFound, discord.HTTPException, AttributeError):
            pass

        if isinstance(member, discord.Member):
            pass
        elif isinstance(member, int):
            try:
                member = await self.bot.fetch_user(member)

            except:
                embed = discord.Embed(description="Invalid ID", color=discord.Color.red())
                await ctx.send(embed=embed)
                return
        else:
            embed = discord.Embed(description="Valid Arguments: `ID` `Member`",
                                  color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        data = []

        avh_DB = sqlite3.connect("avhistory.db")
        avh_cursor = avh_DB.cursor()

        # we store the avatar history data in  list of dicts
        for date, id, url, idAV in get_avatar_history(avh_cursor, member.id):
            data.append(
                {
                    "date": date,
                    "url": url,
                    "id": id,
                    "idAV": idAV
                })

        if len(data) == 0:
            embed = discord.Embed(
                description="No Avatars",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            return

        pagination_view = AvatarHistoryView(timeout=120)
        pagination_view.data = data

        pagination_view.user = member
        pagination_view.author_id = ctx.author.id
        pagination_view.ctx = ctx
        await pagination_view.send(ctx)

    @commands.command()
    async def collectavatars(self, ctx):
        """
        Script that collects avatars of members in the guild.
        Buggy due to limited api requests
        """
        print("test")

        avh_DB = sqlite3.connect('avhistory.db')
        avh_cursor = avh_DB.cursor()
        avh_create_table(avh_cursor, avh_DB)

        # print(ctx.guild.members)

        channel = self.bot.get_channel(1057132789935394908)
        now = str(datetime.datetime.now())

        guild = self.bot.get_guild(739175633673781259)
        new = 0

        print(len(guild.members[-150:-130]))

        for mem in guild.members[-200:-130]:

            print(type(mem))
            avatars = [mem.avatar, mem.display_avatar]
            avatars = [x for x in avatars if x is not None]
            avatars = [x for x in avatars if url_not_in_DB(avh_cursor, str(x))]
            print(avatars)
            avatars = list(set(avatars))

            if len(avatars) == 0:
                continue
            for av in avatars:

                file_name = f"{av.key}.{'gif' if av.is_animated() else 'png'}"
                file_bytes = await av.read()

                text = f"{mem}'s avatar (ID: {mem.id})"
                if mem:
                    text += f" {mem.mention}"
                m = await channel.send(
                    file=discord.File(io.BytesIO(file_bytes), filename=file_name),
                    content=text,
                    allowed_mentions=discord.AllowedMentions.none()
                )
                url = m.attachments[0].url
                entry_avatar(avh_cursor, avh_DB, now, mem.id, url, str(av))
                new += 1
                print(url)

        embed = discord.Embed(
            description=f"{new} Avatars Collected",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AvHistory(bot))
