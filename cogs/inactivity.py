from misc.rover import robloxToDiscord, discordToRoblox
from misc.paginator import Pagination
from discord import app_commands, ui
from discord.utils import get
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
from typing import Literal  
import os
import time 
import pprint
import discord
import json
import hmac
import hashlib
import requests

intents = discord.Intents.all()
intents.members = True
ID_API_ENDPOINT = "https://users.roblox.com/v1/usernames/users"

load_dotenv()
server_id = os.getenv('SERVER_ID')
fc_secret = os.getenv('API_SECRET')
rover_token = os.getenv('ROVER_KEY')
fc_api_key = os.getenv('API_KEY')
inactivity_channel = int(os.getenv("INACTIVITY_CHANNEL"))

mod_id = os.getenv('MOD_ID')
sm_id = os.getenv('SM_ID')
gm_id = os.getenv('GM_ID')
tm_id = os.getenv('TM_ID')

observation_access = int(os.getenv('OBS_ROLE'))

bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree

def getUserId(username, interaction = None):
    requestPayload = {
            "usernames": [
                username
            ],
            "excludeBannedUsers": True # Whether to include banned users within the request, change this as you wish
           }
        
    responseData = requests.post(ID_API_ENDPOINT, json=requestPayload)
        
    assert responseData.status_code == 200
        
    userId = responseData.json()["data"][0]["id"]
        
    print(f"getUserId :: Fetched user ID of username {username} -> {userId}")
    return userId

def getRankInGroup(userid):
    if userid:
        request = requests.get(f"https://groups.roblox.com/v1/users/{userid}/groups/roles")
        response = json.loads(request.text)
        for i in response["data"]:
            if i["group"]["id"] == 2568175:
                return i["role"]["name"]
    else:
        error = "User ID couldn't be found or user not in group."
        return error

def postEvent(api_key, app_id, title, description, start_date, end_date):
    timestamp = int(time.time() * 1000)  
    hash_bytes = hmac.new(fc_secret.encode(), (fc_api_key + str(timestamp)).encode(), hashlib.sha1).digest()
    hash_string = hash_bytes.hex()
    url = f"https://freedcamp.com/api/v1/events"
    params = {
        "api_key": api_key,
        "hash": hash_string,
        "timestamp": timestamp
    }
    data = {
        "title": title,
        "description": description,
        "project_id": app_id,
        "f_all_day": 1,
        "date_start": start_date,
        "date_end": end_date
    }

    response = requests.post(url, json=data, params=params)

    if response.status_code == 200:
        r = response.json()
        __import__('pprint').pprint(response.text)
    else:
        print(f"postEvent:: {response.text}")


def correctRankId(chosenRank):
    match chosenRank:
        case "Gamemaster":
            return gm_id
        case "Trial Moderator":
            return tm_id
        case "Moderator":
            return mod_id
        case "Senior Moderator":
            return sm_id

class AcceptUi(discord.ui.View):
    def __init__(self, start_date, end_date, user, reason, usernameRover, userIdRover, originalInteraction, message, *, timeout=None):
        super().__init__(timeout=timeout)
        self.start_date = start_date
        self.end_date = end_date
        self.user = user
        self.reason = reason
        self.usernameRover = usernameRover
        self.userIdRover = userIdRover
        self.originalInteraction = originalInteraction
        self.message = message 

    @discord.ui.button(label="Accept inactivity notice",style=discord.ButtonStyle.green)
    async def accept_button(self, interaction:discord.Interaction,button:discord.ui.Button):
        role = interaction.guild.get_role(observation_access)
        if role not in interaction.user.roles:
            await interaction.response.send_message("https://i.kym-cdn.com/photos/images/newsfeed/002/916/147/ec1.jpg", ephemeral=True)
            return
        await self.message.edit(content=f":white_check_mark: Inactivity notice accepted by {interaction.user}",view=None)
        postEvent(fc_api_key, correctRankId(getRankInGroup(self.userIdRover)), f"{self.usernameRover} :: Inactivity notice", f"Reason: {self.reason}", self.start_date, self.end_date)

    @discord.ui.button(label="Decline inactivity notice",style=discord.ButtonStyle.red)
    async def decline_button(self, interaction:discord.Interaction,button:discord.ui.Button):
        role = interaction.guild.get_role(observation_access)
        if role not in interaction.user.roles:
            await interaction.response.send_message("https://i.kym-cdn.com/photos/images/newsfeed/002/916/147/ec1.jpg", ephemeral=True)
            return
        await self.message.edit(content=f":x: Inactivity notice denied by {interaction.user}",view=None)

class Inactivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name="inactivity-notice",
        description="Make an inactivity notice"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @app_commands.describe(start_date="Syntax: YYYY-MM-DD", end_date="Syntax: YYYY-MM-DD")
    @discord.app_commands.checks.has_any_role("Game Staff")
    async def inactivity(self, interaction:discord.Interaction, start_date: str, end_date:str, reason:str):
        await interaction.response.defer(ephemeral=True)
        channel = interaction.client.get_channel(inactivity_channel)
        roverResponse = discordToRoblox(rover_token, server_id, interaction.user.id)
        response_data = await roverResponse 
        usernameRover = response_data["cachedUsername"]
        userIdRover = response_data["robloxId"]
        embed = discord.Embed(title=f"Inactivity notice from {interaction.user} ({usernameRover})",
                      colour=0x00b0f4)

        embed.add_field(name="From:",
                        value=start_date,
                        inline=False)
        embed.add_field(name="Until:",
                        value=end_date,
                        inline=False)
        embed.add_field(name="Reason:",
                        value=reason,
                        inline=False)

        message = await channel.send(embed=embed)
        __import__('pprint').pprint(message.id)
        view = AcceptUi(start_date, end_date, interaction.user, reason, usernameRover, userIdRover, interaction, message)
        await message.edit(embed=embed,view=view)
        await interaction.followup.send("Sent!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Inactivity(bot), guild=discord.Object(id=server_id))
