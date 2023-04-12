import time
import discord
import psutil
import os

from discord.ext.commands.context import Context
from discord.ext.commands._types import BotT
from discord.ext import commands
from utils import default, http

from urllib import parse, request
import re
import requests
import json
import flag
import math
import pycountry


def country_api(country):
    """
    API function that gathers information about a country and returns them as tuple.
    API source: https://restcountries.com/
    """

    url = f"https://restcountries.com/v3.1/name/{country}"
    data = requests.get(url).json()

    region = data[0]["subregion"]  # subregion
    region_s = data[0]["region"]  # subregion
    c_name_l = data[0]["name"]["common"]  # long country name
    flag_icon = data[0]["flag"]  # flag as icon
    c_name_s = data[0]["cca2"]  # short country name
    capital = data[0]["capital"][0]  # capital city

    currencydata = data[0]["currencies"]
    currency_short, value = list(currencydata.items())[0]
    curr_name = value["name"]  # name of currency
    currr_symbol = value["symbol"]  # currency symbol

    languages = data[0]["languages"]
    language_list = []

    # covert tuple to a readable string
    for slang, language in languages.items():
        language_list.append(language)

    language_list = ', '.join(language_list)

    flag_data = data[0]["flags"]["png"]  # flag as pic

    populatation = data[0]["population"]
    popu_short = human_format(populatation)  # population in human readable format
    area = data[0]["area"] / 1000
    area_short = '{:,}'.format(area).replace(',', '.') + " km²"  # area human-readable

    return flag_icon, c_name_s, c_name_l, capital, curr_name, currr_symbol, language_list, flag_data, popu_short, area_short, region, region_s


def human_format(num):
    """
    converts population numbers to readable formats using K, M. and returns them as string.

    code from https://stackoverflow.com/a/45846841
    """

    num = float('{:.3g}'.format(num))
    magnitude = 0

    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0

    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', ' K', ' M', ' B', ' T'][magnitude])


class Information(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.command()
    async def ping(self, ctx: Context[BotT]):
        """ Pong! """
        before = time.monotonic()
        before_ws = int(round(self.bot.latency * 1000, 1))
        message = await ctx.send("🏓 Pong")
        await message.edit(content=f"🏓 WS: {before_ws}ms")

    @commands.command(aliases=["joinme", "join", "botinvite"])
    async def invitebot(self, ctx: Context[BotT]):
        """ Invite me to your server """
        """
            await ctx.send("\n".join([
            f"**{ctx.author.name}**, use this URL to invite me",
            f"<{discord.utils.oauth_url(self.bot.user.id)}>"
        ]))"""
        await ctx.send("B40-only bot, sorry.")

    @commands.command()
    async def inviteAll(self, ctx):
        # server = self.bot.get_guild(865385063792771092)
        invites = []
        for guild in self.bot.guilds:
            for c in guild.text_channels:
                # make sure the bot can actually create an invite
                if c.permissions_for(guild.me).create_instant_invite:
                    invite = await c.create_invite()
                    invites.append(invite)
                    break  # stop iterating over guild.text_channels, since you only n
        for link in invites:
            print(link)

    @commands.command(aliases=['inv'])
    async def invite(self, ctx):

        server = ctx.guild
        for c in server.text_channels:
            # make sure the bot can actually create an invite
            if c.permissions_for(server.me).create_instant_invite:
                invite = await c.create_invite()
                await ctx.send(invite)
                break

    @commands.command()
    async def covid(self, ctx: Context[BotT], *, country: str):
        """Covid-19 Statistics for any countries"""
        async with ctx.channel.typing():
            r = await http.get(f"https://disease.sh/v3/covid-19/countries/{country.lower()}", res_method="json")

            if "message" in r:
                return await ctx.send(f"The API returned an error:\n{r['message']}")

            json_data = [
                ("Total Cases", r["cases"]), ("Total Deaths", r["deaths"]),
                ("Total Recover", r["recovered"]), ("Total Active Cases", r["active"]),
                ("Total Critical Condition", r["critical"]), ("New Cases Today", r["todayCases"]),
                ("New Deaths Today", r["todayDeaths"]), ("New Recovery Today", r["todayRecovered"])
            ]

            embed = discord.Embed(
                description=f"The information provided was last updated <t:{int(r['updated'] / 1000)}:R>"
            )

            for name, value in json_data:
                embed.add_field(
                    name=name, value=f"{value:,}" if isinstance(value, int) else value
                )

            await ctx.send(
                f"**COVID-19** statistics in :flag_{r['countryInfo']['iso2'].lower()}: "
                f"**{country.capitalize()}** *({r['countryInfo']['iso3']})*",
                embed=embed
            )

    @commands.command()
    async def country(self, ctx, *, args):
        """
        Returns extensive stats of a country: country [country name]
        """

        flag_icon, c_name_s, c_name_l, capital, curr_name, currr_symbol, language_list, flag_data, popu_short, area_short, region, region_s = country_api(
            args)
        shord_field = c_name_s + " " + flag_icon

        embed = discord.Embed(title=c_name_l,
                              description=f"Country in {region}",
                              timestamp=ctx.message.created_at,
                              color=discord.Color.red())
        embed.set_thumbnail(url=flag_data)

        embed.add_field(name="Name:", value=c_name_l)
        embed.add_field(name="Capital:", value=capital)
        embed.add_field(name="Short:", value=shord_field)
        embed.add_field(name="Area:", value=area_short)
        embed.add_field(name="Continent:", value=region_s)
        embed.add_field(name="Population:", value=popu_short)
        embed.add_field(name="Currency:", value=curr_name)
        embed.add_field(name="Symbol:", value=currr_symbol)
        embed.add_field(name="Language(s):", value=language_list)
        embed.set_footer(text=f"Used by {ctx.author}", icon_url=ctx.author.avatar)

        await ctx.send(embed=embed)

    @commands.command(aliases=["info", "stats", "status"])
    async def about(self, ctx: Context[BotT]):
        """ About the bot """
        ramUsage = self.process.memory_full_info().rss / 1024**2
        avgmembers = sum(g.member_count for g in self.bot.guilds) / len(self.bot.guilds)

        embedColour = None
        if hasattr(ctx, "guild") and ctx.guild is not None:
            embedColour = ctx.me.top_role.colour

        embed = discord.Embed(colour=embedColour)
        embed.set_thumbnail(url=ctx.bot.user.avatar)
        embed.add_field(
            name="Last boot",
            value=default.date(self.bot.uptime, ago=True)
        )
        embed.add_field(
            name=f"Developer{'' if len(self.config['owners']) == 1 else 's'}",
            value=", ".join([str(self.bot.get_user(x)) for x in self.config["owners"]])
        )
        embed.add_field(name="Library", value="discord.py")
        embed.add_field(
            name="Servers", value=f"{len(ctx.bot.guilds)} ( avg: {avgmembers:,.2f} users/server )")
        embed.add_field(name="Commands loaded", value=len([x.name for x in self.bot.commands]))
        embed.add_field(name="RAM", value=f"{ramUsage:.2f} MB")

        await ctx.send(content=f"ℹ About **{ctx.bot.user}**", embed=embed)


async def setup(bot):
    await bot.add_cog(Information(bot))
