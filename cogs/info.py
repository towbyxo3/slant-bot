import time
import discord
import psutil
import os

from discord.ext.commands.context import Context
from discord.ext.commands._types import BotT
from discord.ext import commands
from utils import default, http

from urllib import parse, request
import requests
import json


def get_country_information(country):
    """
    API function that gathers information about a country and returns them as a dictionary.
    API source: https://restcountries.com/

    country: country for which information should be retrieved

    c - country
    s - short
    l - long
    """
    url = f"https://restcountries.com/v3.1/name/{country}"
    data = requests.get(url).json()

    country_data = {}

    country_data["region"] = data[0]["subregion"]
    country_data["region_s"] = data[0]["region"]
    country_data["c_name_l"] = data[0]["name"]["common"]
    country_data["flag_icon"] = data[0]["flag"]
    country_data["c_name_s"] = data[0]["cca2"]
    country_data["capital"] = data[0]["capital"][0]

    currencydata = data[0]["currencies"]
    currency_short, value = list(currencydata.items())[0]
    country_data["curr_name"] = value["name"]
    country_data["currr_symbol"] = value["symbol"]

    languages = data[0]["languages"]
    language_list = []

    # convert tuple to a readable string
    for slang, language in languages.items():
        language_list.append(language)

    country_data["language_list"] = ', '.join(language_list)

    country_data["flag_data"] = data[0]["flags"]["png"]

    population = data[0]["population"]
    country_data["popu_short"] = convert_to_readable_format(population)

    area = data[0]["area"] / 1000
    country_data["area_short"] = '{:,}'.format(area).replace(',', '.') + " km²"

    return country_data


def convert_to_readable_format(num):
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
        before_ws = int(round(self.bot.latency * 1000, 1))
        message = await ctx.send("🏓 Pong")
        await message.edit(content=f"🏓 WS: {before_ws}ms")

    @commands.command()
    async def myservers(self, ctx):
        """
        Creates invite links for every server the bot is in.
        """
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
        """
        Returns invite for this server.
        """
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
        Returns extensive stats of a country.
        """

        country_data = get_country_information(args)

        embed = discord.Embed(
            title=country_data["c_name_l"],
            description=f"Country in {country_data['region']}",
            timestamp=ctx.message.created_at,
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=country_data["flag_data"])

        field_data = {
            "Name:": country_data["c_name_l"],
            "Capital:": country_data["capital"],
            "Short:": country_data["c_name_s"] + " " + country_data["flag_icon"],
            "Area:": country_data["area_short"],
            "Continent:": country_data["region_s"],
            "Population:": country_data["popu_short"],
            "Currency:": country_data["curr_name"],
            "Symbol:": country_data["currr_symbol"],
            "Language(s):": country_data["language_list"]
        }

        for name, value in field_data.items():
            embed.add_field(name=name, value=value)

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

    @commands.command(aliases=["git", "repository", "repo", "sourcecode"])
    async def github(self, ctx):
        embed = discord.Embed(
            title="Source Code",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="https://i.imgur.com/E0BMWj8.png")
        embed.add_field(
            name="GitHub Repository",
            value="[towbyxo3/slant-python-discord-bot](https://github.com/towbyxo3/slant-python-discord-bot)",
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["helpcommand"])
    async def help(self, ctx):
        embed = discord.Embed(color=discord.Color.green(), title="Help Command")
        embed.set_thumbnail(url="https://i.imgur.com/E0BMWj8.png")
        embed.add_field(
            name="Overview of Bot Commands",
            value="[Command List](https://towbyxo3.github.io/tobo)",
        )
        embed.set_footer(text="Last updated: 22.05.2023")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Information(bot))
