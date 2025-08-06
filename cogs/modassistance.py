import discord
import requests
import sqlite3
from discord import app_commands, Embed, ui
from discord.utils import get
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
from typing import Literal
import os
import time 
import pprint

intents = discord.Intents.all()
intents.members = True

ID_API_ENDPOINT = "https://users.roblox.com/v1/usernames/users"
load_dotenv("../.env")
server_id = os.getenv('SERVER_ID')
assistance_channel = os.getenv('ASSISTANCE_CHANNEL')

# ts converts roblox username to roblox id
def getUserId(username):
    requestPayload = {
            "usernames": [
                username
            ],
            "excludeBannedUsers": True # Whether to include banned users within the request, change this as you wish
           }
        
    responseData = requests.post(ID_API_ENDPOINT, json=requestPayload)
        
            # Make sure the request succeeded
    assert responseData.status_code == 200
        
    userId = responseData.json()["data"][0]["id"]
        
    print(f"getUserId :: Fetched user ID of username {username} -> {userId}")
    return userId

# converts username to user headshot
def getHeadshot(roblox_username):
    userRawHeadshot = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={getUserId(roblox_username)}&format=png&size=352x352"
    response = requests.get(userRawHeadshot)
    if response.status_code == 200:
        userParsedHeadshot = response.json()
        userFinalHeadshot = userParsedHeadshot['data'][0]['imageUrl']
        print(f"getHeadshot :: Fetched headshot of {roblox_username}")
        return userFinalHeadshot
    else:
        placeholderImg = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fi.imgflip.com%2Fd0tb7.jpg&f=1&nofb=1&ipt=e1c23bf6c418254a56c19b09cc9ece6238ead393652e54278f0d535f9fb81c56"
        return placeholderImg


class Assistance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name="mod-assistance",
        description="Call for mod assistance for in-game support"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def assistance(self, interaction:discord.Interaction, urgency:Literal["Low","Medium", "High"], roblox_username: str, description:str, server_era: str):
        embed = discord.Embed(title=f"Assistance needed in {server_era}!",
                      url=f"https://www.roblox.com/users/{getUserId(roblox_username)}/profile",
                      colour=0x00b0f4)

        embed.set_author(name=interaction.user,
                         url=f"https://www.roblox.com/users/{getUserId(roblox_username)}/profile",
                         icon_url=interaction.user.avatar.url)
        
        embed.add_field(name="Urgency",
                        value=urgency,
                        inline=False)

        embed.add_field(name="Caller",
                        value=f"{interaction.user} ({roblox_username})",
                        inline=False)
        embed.add_field(name="description",
                value=description,
                inline=False)

        embed.add_field(name="Era",
                value=server_era,
                inline=False)
        embed.set_thumbnail(url=getHeadshot(roblox_username))

        assistance_channel_parsed = interaction.client.get_channel(int(assistance_channel))

        message = await assistance_channel_parsed.send(embed=embed)
        thread = await message.create_thread(name=f"{urgency} :: {roblox_username}")
        await thread.send(f"<@{interaction.user.id}> :: <@&1030362803757924452>")
        await interaction.response.send_message("Sent!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Assistance(bot), guild=discord.Object(id=server_id))
