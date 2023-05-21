## Table of Contents

- [Admin](#admin) (Commands related to bot administration)
- [Info](#info) (Commands for retrieving information about members and servers)
- [Leaderboard](#leaderboard) (Commands for displaying leaderboard statistics)
- [Mod](#mod) (Commands for moderating and managing members and server)
- [Prune](#prune) (Commands for pruning and deleting messages)
- [Fun](#fun) (Fun commands for interactive features)
- [Voicechat](#voicechat) (Commands for moving members in voice channels)

---

Command [Possible Arguments]: Description

---

## Admin
- **owner** []:
Returns the owner.
- **load** [cog name]: 
Loads an extension.
- **unload** [cog name]: 
Unloads an extension.
- **reload** [cog name]: 
Reloads an extension.
- **reloadall** []:
Reloads all extensions.
- **reloadutils** [util name]: 
Reloads utils. 
---
- **change playing** [status]: 
Change the status of the bot.
- **change username** [username]: 
Change the username of the bot.
- **change nickname** [nickname]: 
Change the nickname of the bot.
- **change avatar** [picture url/file]: 
Change the avatar of the bot.

---

## Info
- **avatar** [member]: \
Displays the current and past profile pictures of members, both global and server-specific,  
since joining the server.  
Option to delete the avatar if it's the member who used that avatar.
- **serverinfo** []:
Returns information about the current server.  
Option to display icon and banner of server.
- **userinfo** [member]: 
Returns information about the user.
- **names** [member]: 
Returns the previous usernames/nicknames of the user.
- **banner** [member]: 
Returns the banner of the user.
- **collectavatars** []:
Stores avatars of members in the current guild.
---
- **about** []:
Returns stats and information about the bot.
- **ping** []:
Returns the ping of the bot.
- **invite** []:
Returns the invite link for the current server.
- **myservers** []:
Prints invite links to the bot's servers in the console.
- **github** []:
Returns the link to this GitHub repository.
---
- **covid** [country]: 
Returns COVID statistics of a country.
- **country** [country]: 
Returns general information about a country.

---

## Leaderboard

- **crowns** [member]: 
Displays members with the most crowns.  
A crown is earned for every day the member sent the most messages.
- **age** []:
Displays the youngest or oldest members based on a criteria.
        [by registration date] [by server join date]
- **chat** [member]: Displays members with the most messages in selected timeframe.  
        [current week] [current month] [current year] [alltime]

- **mentions** [member]: Displays mention leaderboard and stats of the server and member.
        [server-wide most mentions] [Tagged by (member)] [(member) Tagged]

- **serverpeak** []:
Displays timeframes where most messages were sent in the server.
        [days] [weeks] [months] [years]
- **userpeak** [member]: 
Displays timeframes where a  member sent the most messages in the server.
        [days] [weeks] [months] [years]

---

## Mod
- **kick** [member]: 
Kicks a member from the server.
- **nickname** [member]: 
Changes the nickname of a member.
- **ban** [member]: 
Bans a member from the server.
- **massban** [member, member, ..]: 
Bans several members from the server.
- **unban** [member.id]: 
Unbans a user from the server.
---
- **prune embeds** [count]: 
Removes a certain number of recently sent embeds in the chat.
- **prune files** [count]: 
Removes a certain number of recently sent files in the chat.
- **prune mentions** [count]: 
Removes a certain number of recently sent mentions in the chat.
- **prune images** [count]: 
Removes a certain number of recently sent images in the chat.
- **prune all** [count]: 
Removes every recently sent message.
- **prune user** [count]: 
Removes a certain number of recently sent messages by a member.
- **prune contains** [count]: 
Removes a certain number of recently sent messages that contain a phrase.
- **prune bots** [count]: 
Removes a certain number of recently sent messages by bots.
- **prune users** [count]: 
Removes a certain number of recently sent messages by users.
- **prune reactions** [count]: 
Removes a certain number of recently added reactions.

---

## Fun
- **network** [member]: \
Returns the most frequent chat encounters of a member graphically. The numbers on the graph indicate the number of times that a member and the other person chatted within the same 5-minute time frame.

- **wordcloud** [member, min word length]: 
Returns a wordcloud that shows the most frequently used words by a member graphically.
- **wordcloudserver** [min word length]: 
Returns a wordcloud that shows the most frequently used words in the server graphically.
- **said** [word]: 
Returns members who most frequently used the word.

- **rewind** [member, year]: \
Returns an embed with clickable rewind pictures and stats of a year. The embed contains 6 pictures that display the most notable member chat stats of a particular year.
- **rewindserver** [year]: \
Returns an embed with clickable rewind pictures and stats of a year. The embed contains 6 pictures that display the most notable server chat stats of a particular year.

- **quote** [member, word/phrase]: 
Returns a random message (by a member) that contains a certain phrase or word.

- **snipe** [member]: 
Returns the last deleted message (by a member).
- **snip** [member]: 
Returns the last edited message (by a member).

---

## Voicechat
- **massmove** [voice channel]: 
Moves members in the current channel to a certain channel.
- **massmoveall** [voice channel]: 
Moves all members who are in a voice channel to a certain channel.

---
