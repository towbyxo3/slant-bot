![Slant Logo](./README/00_slant.gif)
# Slant Server Discord BOT
This is a Discord bot written in Python for a server with a group of friends and friends of friends. The bot is designed to make the server more fun and engaging by providing a range of useful features and commands.

# Features
The BOT has around 60 different commands and features which include very basic (like USERINFO, SERVERINFO, AVATAR, KICK, BAN, etc.) and many unique and server dedicated ones.  
Some of which are showcased in the next chapter.  
[Command List](README/command_list.txt)

## Welcome Message with AI Background Pictures
Posts a welcome picture including the name and avatar of the newly joined member.

![Welcome Message example](./README/01_welcome.PNG)

The bot uses a random picture out of 25 AI made background pictures to create the welcome message.

![Welcome Message example](./README/02_welcome_background_examples.PNG)

## TIKTOK Downloader
Automatically downloads any TikTok links and posts the video as reply to the original message within seconds. This way, the sent TikTok is viewable directly on Discord.

![TT downloader example](./README/14_TIKTOK_downloader.PNG)

## Chat Leaderboard
Showcases Members with most messages in a time period (weekly, monthly, yearly or all-time)
![Chat LB example](./README/04_leaderboard_chat.gif)

## Crowns
Shows a leaderboard of members with the most crowns.
You obtain a crown for every day you were the member with most messages sent.

![Crowns example](./README/13_crowns.PNG)

## Wordcloud
Creates a wordcloud of the words used by a member on the server. This command is useful for analyzing the most commonly used words.

![Wordcloud example](./README/03_word_cloud.PNG)

## Avatar History 
Showcases the profile pictures used by a member since joining the server. 

![Avatar history example](./README/05_avatar_history.gif)

## Rewind
Showcases various chat stats graphically including most active weekday of the week, time of the day etc..

![Rewind example](./README/06_rewind.gif)

## Network
Showcases a network graph with members who chat at similar times as the member.

![Network example](./README/07_network.PNG)

## User Messages Peak Leaderboard
Showcases messages peaks by members within a timeframe (most messages in one day, one week, one month, one year by a single member))

![User messages peak example](./README/08_peak_messages_user.gif)

## Snipe
Showcases last deleted message in used text channel.

![Snipe example](./README/09_snipe.PNG)

## Said
Shows a leaderboard of members who used a particular word the most.

![Word example](./README/12_said.PNG)

## Msg
Finds a random past message (by a member containing a word/phrase)

![Msg example](./README/15_msg.PNG)

## Country
Shows basic information about a country.

![Country example](./README/10_country.PNG)

# HOW TO INSTALL

## 1. Clone repository 
`git clone https://github.com/towbyxo3/slant-python-discord-bot.git`
## 2. Install packages 
`pip install -r requirements.txt`
## 3. Modify config.json
Insert your bots token and your ID into the config.json file and modify settings to your liking.
## 4. Run the BOT.
`python3 index.py`  
or  
`python index.py`


