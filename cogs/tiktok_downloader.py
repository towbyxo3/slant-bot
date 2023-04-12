import discord
from utils import default
from discord.ext import commands
import os
import re
import yt_dlp


def download_tiktok_video(url):
    """
    Downloads TikTok video from url, returns filename.

    url: url of the video
    """
    ydl_opts = {
        'format': 'download_addr-0',
        'outtmpl': '%(title)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        filename = ydl.prepare_filename(info_dict)
        ydl.download([url])
        return filename


class Tiktok(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.config = default.load_json()

    @commands.Cog.listener()
    async def on_message(self, message):
        # Use regex to find TikTok URLs in the message
        pattern = r'(https?://[^\s]+tiktok\.com/[^\s]+)'
        match = re.search(pattern, message.content)
        if match:
            url = match.group(1)
        else:
            return

        try:
            filename = download_tiktok_video(url)
        except:
            return
        file = discord.File(filename)
        await message.channel.send(file=file, reference=message)
        os.remove(filename)


async def setup(bot):
    await bot.add_cog(Tiktok(bot))
