import sqlite3
import discord
import psutil
import os
import datetime
import io
import sys
from discord.ext import commands
from utils import default
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

    db: database
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
    Fetches all avatars of a user from the avatar history database

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
    View to display an embed showing the user's current avatar(s).
    Toggle ability between global and server avatar if server avatar exists.
    Additionally, there is a "History" button that, when clicked,
    displays the user's avatar history.
    """
    GLOBAL_AV = 1
    SERVER_AV = 2

    # represents current page number, default is 1
    current_page: int = 1
    # whether the the history button has been used yet
    history_button_trigger = False

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
        if self.current_page == 1:
            av = self.user.display_avatar if self.user.avatar is None else self.user.avatar
        elif self.current_page == 2:
            av = self.user.display_avatar

        embed = discord.Embed(
            title="Avatar",
            color=self.user.color
        )

        embed.set_author(
            name=f"{self.user.name} # {self.user.discriminator}",
            icon_url=self.user.display_avatar
        )
        embed.set_image(url=av)

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
        page 1 - global avatar
        page 2 - server avatar
        """
        # logic to determine if a member has a server avatar
        has_server_avatar = (self.user.avatar != self.user.display_avatar) and (self.user.avatar is not None)
        if self.current_page == self.GLOBAL_AV:
            self.global_avatar.disabled = True
            self.server_avatar.disabled = not has_server_avatar
            self.global_avatar.style = discord.ButtonStyle.gray
            self.server_avatar.style = discord.ButtonStyle.blurple if has_server_avatar else discord.ButtonStyle.gray

        if self.current_page == self.SERVER_AV:
            self.global_avatar.disabled = False
            self.server_avatar.disabled = True
            self.global_avatar.style = discord.ButtonStyle.blurple
            self.server_avatar.style = discord.ButtonStyle.gray

        # history button is disabled after its triggered to avoid spam
        if self.history_button_trigger is True:
            self.history.disabled = True
            self.history.style = discord.ButtonStyle.gray

    @discord.ui.button(label="Global", style=discord.ButtonStyle.green)
    async def global_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = 1

        await self.update_message()

    @discord.ui.button(label="Server", style=discord.ButtonStyle.primary)
    async def server_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = 2
        await self.update_message()

    @discord.ui.button(label="History", style=discord.ButtonStyle.primary)
    async def history(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        If the history button is pressed, a new additional view (AvatarHistoryView)
        is sent to the channel.
        """
        await interaction.response.defer()
        self.history_button_trigger = True
        await self.update_message()

        data = []

        avh_DB = sqlite3.connect("avhistory.db")
        avh_cursor = avh_DB.cursor()

        # we store the avatar history data in  list of dicts
        for date, id, url, idAV in get_avatar_history(avh_cursor, self.user.id):
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
            await self.ctx.send(embed=embed)
            return

        # create new view with the members avatar history
        pagination_view = AvatarHistoryView(timeout=120)
        pagination_view.data = data

        pagination_view.user = self.user
        pagination_view.author_id = self.ctx.author.id
        pagination_view.ctx = self.ctx
        await pagination_view.send(self.ctx)


class AvatarHistoryView(discord.ui.View):
    """
    Is a view for the avatar history of a member.
    It includes  buttons for navigating through and
    displaying avatar history data.
    """

    # represents the current page of avatar history data being displayed
    current_page: int = 1
    # an integer representing the number of items (1 avatar per page)
    # to display per page
    sep: int = 1

    async def send(self, ctx):
        """
        Send the view to a channel. It creates a message
        containing the view and updates it.
        """
        self.message = await ctx.send(view=self)
        await self.update_message(self.data[:self.sep])

    def create_embed(self, data):
        """
        Creates an embed with the given avatar history data
        """
        embed = discord.Embed(
            title=f"{self.current_page} / {int(len(self.data) / self.sep)}",
            color=self.user.color
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
                    f"Avatar ID: {item['idAV']} • {format_YMD_to_DMY(item['date'][:10])}"
                )
            )
        return embed

    async def update_message(self, data):
        """
        Updates the view's message with the given avatar history data and updates the view's buttons
        """
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(data), view=self)

    def update_buttons(self):
        """
        Updates the state of the view's navigation buttons based on the current page and data being displayed
        """
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

    @discord.ui.button(label="|<", style=discord.ButtonStyle.green)
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = 1

        await self.update_message(self.get_current_page_data())

    @discord.ui.button(label="<", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page -= 1
        await self.update_message(self.get_current_page_data())

    @discord.ui.button(label=">", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page += 1
        await self.update_message(self.get_current_page_data())

    @discord.ui.button(label=">|", style=discord.ButtonStyle.green)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = int(len(self.data) / self.sep)
        await self.update_message(self.get_current_page_data())

    @discord.ui.button(label="DEL", style=discord.ButtonStyle.red)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Deletes the first entry on the current page of avatar history data,
        if the user interacting with the button matches the ID of the member
        whose avatar is being deleted.
        """
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
        self.channel_avatar_history_images = self.config["channel_avatar_history_images"]
        self.my_guild = self.config["my_guild"]

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        """
        Store new member avatars in database.
        """
        if (before.avatar is None) and (after.avatar is None):
            return

        # connect to avatar history database
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

        # for every new and unique avatar, download picture or gif
        for av in avatars:
            try:
                file_name = f"{av.key}.{'gif' if av.is_animated() else 'png'}"
                file_bytes = await av.read()
                # fetch channel where you post the permanent avatar copy
                channel = self.bot.get_channel(self.channel_avatar_history_images)
                text = f"{after}'s avatar (ID: {after.id})"
                member = channel.guild.get_member(after.id)
                if member:
                    text += f" {after.mention}"
                # send the picture as file in a seperate channel,
                m = await channel.send(
                    file=discord.File(io.BytesIO(file_bytes), filename=file_name),
                    content=text,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                # save the attachment url and store the gathered data in a database
                url = m.attachments[0].url
                entry_avatar(avh_cursor, avh_DB, now, after.id, url, str(av))
                print(url)
            except (discord.NotFound, discord.HTTPException, AttributeError):
                pass

    @commands.command(aliases=['av', 'pfp', 'avt', 'pf', 'avh', 'avatarhistory', 'icon', 'picture', 'profilepicture'])
    async def avatar(self, ctx, member: discord.Member = None):
        """
        Displays a members global (and if given, server avatar in a embed view).
        Additonally, you get the option to view a members past avatars and
        to delete them if you're the owner of the avatar.
        """

        if member is None:
            member = ctx.author

        # store current avatars of member in database.
        try:
            avh_DB = sqlite3.connect('avhistory.db')
            avh_cursor = avh_DB.cursor()
            now = str(datetime.datetime.now())
            avatars = list(set([member.display_avatar, member.avatar]))

            for av in avatars:
                if url_not_in_DB(avh_cursor, str(av)):
                    file_name = f"{av.key}.{'gif' if av.is_animated() else 'png'}"
                    file_bytes = await av.read()
                    channel = self.bot.get_channel(self.channel_avatar_history_images)
                    text = f"{member.name}'s avatar (ID: {member.id})"
                    m = await channel.send(
                        file=discord.File(io.BytesIO(file_bytes), filename=file_name),
                        content=text,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                    url = m.attachments[0].url
                    entry_avatar(avh_cursor, avh_DB, now, member.id, url, str(av))
        except (discord.NotFound, discord.HTTPException, AttributeError):
            pass

        pagination_view = AvatarView(timeout=120)
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

        avh_DB = sqlite3.connect('avhistory.db')
        avh_cursor = avh_DB.cursor()
        avh_create_table(avh_cursor, avh_DB)

        # print(ctx.guild.members)

        channel = self.bot.get_channel(self.channel_avatar_history_images)
        now = str(datetime.datetime.now())

        guild = self.bot.get_guild(self.my_guild)
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
