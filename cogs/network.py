import sqlite3
import discord
import psutil
import os
from discord.ext import commands
from utils import default
import pandas as pd
import sys
from collections import defaultdict
import time
import datetime
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patheffects import withStroke


def cmap_purple():
    """
    Returns cmap colours for daytime and daytime/weekday heatmap
    """
    return mcolors.LinearSegmentedColormap.from_list("custom", ["#303434", "purple"])


class network(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()
        self.process = psutil.Process(os.getpid())

    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.command()
    async def network(self, ctx, member: discord.Member = None):
        start = time.time()
        """
        Creates a graphic displaying a members most frequent encounters in the chat

        arg1, arg2: year or @member
        """
        if member is None:
            member = ctx.author

        database = sqlite3.connect("chat.db")
        authorID = member.id
        today = datetime.datetime.now()

        # accessing the year attribute
        year = today.year
        # await ctx.send(year)
        query = """
            SELECT DATETIME(date) as datetime, authorID
            FROM B40
            WHERE STRFTIME('%Y', Date) = '{}'
            """
        data = pd.read_sql_query(query.format(year), database)
        data['datetime'] = pd.to_datetime(data['datetime'])
        data = data.groupby(pd.Grouper(key='datetime', freq='5T')).agg({'AuthorID': lambda x: set(x)})
        data = data[data['AuthorID'].apply(lambda x: authorID in x)]

        conversation_partners = defaultdict(int)
        for _, row in data.iterrows():
            if authorID in row['AuthorID']:
                for partner in row['AuthorID']:
                    if partner != authorID:
                        conversation_partners[partner] += 1

        sorted_partners = sorted(conversation_partners.items(), key=lambda x: x[1], reverse=True)

        amount_partners = 15
        top_partners = sorted_partners[:amount_partners]
        top_partners_with_name = []
        for tupl in top_partners:
            try:
                member_obj = await self.bot.fetch_user(tupl[0])
                if member_obj.bot:
                    continue
                member_name = member_obj.name
                print(member_name)
                top_partners_with_name.append((member_name, tupl[1]))
            except:
                pass

        highest_value = sorted_partners[0][1]
        good_ratio = 2000 / highest_value

        #plt.rcParams['axes.facecolor'] = 'black'
        G = nx.Graph()
        G.add_nodes_from([authorID] + [x[0] for x in top_partners_with_name])
        for x in top_partners_with_name:
            G.add_edge(authorID, x[0], weight=x[1] / 40)

        # shell_layout another decent option
        pos = nx.fruchterman_reingold_layout(G)
        # pos = nx.shell_layout(G)
        # pos = nx.circular_layout(G)
        # pos = nx.spring_layout(G)

        # Draw the nodes
        print(authorID)
        nx.draw_networkx_nodes(G, pos, nodelist=[authorID], node_size=2000, node_color='white')
        nx.draw_networkx_nodes(G, pos, nodelist=[x[0] for x in top_partners_with_name], node_size=[
                               x[1] * good_ratio for x in top_partners_with_name], node_color=[x[1] for x in top_partners_with_name], cmap='RdPu')

        labels = {authorID: f"{member.name}\nYOU"}
        for node, label in labels.items():
            x, y = pos[node]
            plt.text(x, y, label, fontweight='bold', fontsize=12,
                     color='white', ha='center', va='center', path_effects=[withStroke(linewidth=1, foreground='black')])

        # Draw the edges
        nx.draw_networkx_edges(G, pos, edgelist=[(authorID, x[0]) for x in top_partners_with_name],
                               edge_color='grey', width=[x[1] / 500 for x in top_partners_with_name])

        labels = {x[0]: str(x[0]) + '\n' + str(x[1]) for x in top_partners_with_name}

        #nx.draw_networkx_labels(G, pos, labels, font_color='white')

        for node, label in labels.items():
            x, y = pos[node]
            plt.text(x, y, label, fontweight='bold', fontsize=12,
                     color='white', ha='center', va='center', path_effects=[withStroke(linewidth=1, foreground='black')])
        plt. margins(x=0)
        fig = plt.gcf()
        fig.set_size_inches(10, 7)
        fig.savefig("usernetwork.png", dpi=200,
                    transparent=True, bbox_inches='tight')
        plt.clf()
        plt.close()

        file = discord.File("usernetwork.png")
        embed = discord.Embed(description="Network")

        # Set the image URL
        embed.set_image(url="attachment://usernetwork.png")

        # Send the embed message
        await ctx.send(embed=embed, file=file)

        end = time.time()
        print(f'Time taken: {end - start} seconds')


async def setup(bot):
    await bot.add_cog(network(bot))
