from discord import app_commands, ui
from misc.rover import robloxToDiscord, discordToRoblox
from roblox import Client
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
import requests

intents = discord.Intents.all()
intents.members = True

load_dotenv()
server_id = os.getenv('SERVER_ID')
roblosecurity = os.getenv("ROBLOSECURITY")
rover_token = os.getenv('ROVER_KEY')

client = Client(roblosecurity)
bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree
ID_API_ENDPOINT = "https://users.roblox.com/v1/usernames/users"

ranklist = {
        "Participant": 1,
        "Experienced Participant": 5,
        "Trusted Participant": 8,
        "Gamemaster": 10,
        "Trial Moderator": 10,
        "Moderator": 20,
        "Senior Moderator": 30,
        "Retired Staff": 31,
        "Respected Peer": 32
}

def getUserId(username):
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
                return i["role"]["rank"]
    else:
        error = "User ID couldn't be found or user not in group."
        return error

class Bulkmanipluate(discord.ui.Modal, title='Bulk manipulation'):
    body = ui.TextInput(label='Users seperated by newline', placeholder="Amnity\nRockoxe\nArmadaStudios", style=discord.TextStyle.long)
    reason = ui.TextInput(label='Reason', placeholder="Passed application", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        loading = await interaction.followup.send("<a:loading:1424337544891338784> Parsing list...", ephemeral=True)
        userlist = self.body.value.split()
        await loading.edit(content=f"<a:loading:1424337544891338784> Started mass manipulation. Users to manipulate: {len(userlist)}")
        count = 0
        for user in userlist: # user is a username
            time.sleep(2)
            userid = getUserId(user)
            userRank = getRankInGroup(userid)
            keys = [key for key, val in ranklist.items() if val == userRank]
            if keys == [] or userRank == None:
                await loading.edit(content=f"<a:loading:1424337544891338784> {user} has unknown/inaccesible role {userRank}. Skipping... {count}/{len(userlist)}")
                count += 1
            else:
                userRole = str(keys[0])
                if userRank:
                    await loading.edit(content=f"<a:loading:1424337544891338784> Modified {user} from {userRole} {count}/{len(userlist)}")
                    # TODO: add actual rank change here
                    count += 1
                    pass
                elif userRank == 2:
                    await loading.edit(content=f"<a:loading:1424337544891338784> {user} has banished role, skipping... {count}/{len(userlist)}")
                    count += 1
                    pass

        await loading.edit(content=f":white_check_mark: Manipulations complete!")
        # TODO: add sending all ts into logs
        
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
        traceback.print_exception(type(error), error, error.__traceback__)

class Rolemanipulations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name="manipluate-rank",
        description="Edit a users rank."
    )
    @app_commands.guilds(discord.Object(id=server_id))
    #@discord.app_commands.checks.has_any_role("Administrator")
    async def changerank(self, interaction: discord.Interaction, user: discord.Member, rank:Literal[tuple(ranklist.keys())] , reason: str):
        await interaction.response.defer(ephemeral=True)
        loading = await interaction.followup.send("<a:loading:1424337544891338784> Calling Rover...", ephemeral=True)
        rankId = ranklist.get(rank)
        roverResponse = discordToRoblox(rover_token, server_id, interaction.user.id)
        response_data = await roverResponse 
        usernameRover = response_data["cachedUsername"]
        userIdRover = response_data["robloxId"]
        await loading.edit(content="<a:loading:1424337544891338784> Determining manipulation type...")
        if getRankInGroup(userIdRover) > rankId:
            await loading.edit(content="<a:loading:1424337544891338784> Determined as demotion...")
            channel = 1030362797697159240 # demotion logs
        else:
            await loading.edit(content="<a:loading:1424337544891338784> Determined as promotion...")
            channel = 1030362796774400040
        channel = interaction.client.get_channel(channel)
        await channel.send("Test")
        # TODO: add ro.py stuff
        await loading.edit(content=":white_check_mark: Rank changed!")

    @app_commands.command(
        name="manipluate-rank-bulk",
        description="Edit lots of users ranks."
    )
    @app_commands.guilds(discord.Object(id=server_id))
    #@discord.app_commands.checks.has_any_role("Administrator")
    async def changerankbulk(self, interaction: discord.Interaction, rank:Literal[tuple(ranklist.keys())]):
        await interaction.response.send_modal(Bulkmanipluate())

async def setup(bot: commands.Bot):
    await bot.add_cog(Rolemanipulations(bot), guild=discord.Object(id=server_id))
