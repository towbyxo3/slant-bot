import discord

from utils import default
from discord.ext import commands


from discord.ext.commands import check


def in_voice_channel():

    def predicate(ctx):
        return ctx.author.voice and ctx.author.voice.channel

    return check(predicate)


class voicechat(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()

    @in_voice_channel()
    @commands.command()
    async def mm(self, ctx, *, channel: discord.VoiceChannel):
        """
        Moves every person in the current voice channel to a new channel: mm [channel name]
        """

        if ctx.author.guild_permissions.move_members:
            for members in ctx.author.voice.channel.members:
                await members.move_to(channel)
        else:
            await ctx.send("You don't have the permission to use this command!"
                           )

    @commands.command(aliases=['mma'])
    async def mmall(self, ctx, *, channel: discord.VoiceChannel):
        """
        Moves every member of the server who is in a voice channel to a certain voice channel.: mmall [channel name]
        """

        if ctx.author.guild_permissions.move_members:
            for channelz in ctx.guild.voice_channels:
                for members in channelz.members:
                    await members.move_to(channel)
        else:
            await ctx.send("You don't have the permission to use this command!"
                           )


async def setup(bot):
    await bot.add_cog(voicechat(bot))
