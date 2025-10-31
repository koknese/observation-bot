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
import aiohttp
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
class PromotionMessage(ui.LayoutView):
    def __init__(self, *, finalString:str, user: int, reason:str) -> None:
        super().__init__()
        self.promotionText = ui.TextDisplay(finalString)
        self.separator = ui.Separator(visible=True)
        self.reasonText = ui.TextDisplay(reason)
        self.promoter = ui.TextDisplay(f"-# Rank changed by <@{user}>")
        container = ui.Container(
                self.promotionText,
                self.separator,
                self.reasonText,
                self.separator,
                self.promoter,
                accent_color=discord.Color.blurple()
        )
        self.add_item(container)

async def getUserId(username):
    requestPayload = {
        "usernames": [
            username
        ],
        "excludeBannedUsers": True  # Whether to include banned users within the request, change this as you wish
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(ID_API_ENDPOINT, json=requestPayload) as response:
            assert response.status == 200
            
            responseData = await response.json()
            userId = responseData["data"][0]["id"]
            
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
    def __init__(self,rank):
        super().__init__()
        self.rank = rank

    body = ui.TextInput(label='Users seperated by newline', placeholder="Amnity\nRockoxe\nArmadaStudios", style=discord.TextStyle.long)
    reason = ui.TextInput(label='Reason', placeholder="Passed application", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        group = await client.get_group(2568175)
        manipulated = {
                # "Participant": ["Player", "AnotherOne"], 
        }
        await interaction.response.defer(ephemeral=True)
        loading = await interaction.followup.send("<a:loading:1424337544891338784> Parsing list...", ephemeral=True)
        userlist = self.body.value.split()
        await loading.edit(content=f"<a:loading:1424337544891338784> Started mass manipulation. Users to manipulate: {len(userlist)}")
        count = 1
        for user in userlist: # user is a username
            time.sleep(2)
            userid = await getUserId(user)
            userRank = getRankInGroup(userid) # Numeric rank
            keys = [key for key, val in ranklist.items() if val == userRank]
            if keys == [] or userRank == None:
                await loading.edit(content=f"<a:loading:1424337544891338784> {user} has unknown/inaccesible role {userRank}. Skipping... {count}/{len(userlist)}")
                count += 1
            else:
                userRole = str(keys[0])
                if userRank:
                    await loading.edit(content=f"<a:loading:1424337544891338784> Modified {user} from {userRole} {count}/{len(userlist)}")
                    await group.set_rank(userid, ranklist[self.rank]) #TODO: uncomment when done
                    # Checks whether there is a key in the manipulated dict that matches users role
                    roverResponse = robloxToDiscord(rover_token, server_id, userid)
                    response_data = await roverResponse 
                    if response_data == None:
                        userIdRover = "(Not in Riskord)"
                        pass
                    else:
                        userIdRover = response_data["discordUsers"][0]["user"]["id"]
                        pass
                    if userRole in manipulated:
                        userArray = manipulated[userRole] # gets tge corresponding array
                        userArray.append(f"{user} (<@{userIdRover}>)") # append the username to the array
                    else:
                        manipulated.update({userRole: [f"{user} <@{userIdRover}>"]}) # if no key found then make one and make the value an array and add the user there
                    count += 1
                    pass
                elif userRank == 2:
                    await loading.edit(content=f"<a:loading:1424337544891338784> {user} has banished role, skipping... {count}/{len(userlist)}")
                    count += 1
                    pass
        await loading.edit(content=f":white_check_mark: Manipulations complete!")
        finalString = f""
        for rank in manipulated:
            res = "\n".join(manipulated[rank])
            res = f"{res}\n**{rank} --> {self.rank}**\n\n"
            finalString += res

        # determining in which channel should we send the message via comparing the rank of the first user and the rank chosen
        # TODO: switch to actual channels
        if ranklist[self.rank] < ranklist[next(iter(manipulated))]:
            channel = interaction.client.get_channel(1030362797697159240)
            await channel.send(view=PromotionMessage(finalString=finalString, user=interaction.user.id, reason=self.reason.value))
        else:
            channel = interaction.client.get_channel(1030362796774400040)
            await channel.send(view=PromotionMessage(finalString=finalString, user=interaction.user.id, reason=self.reason.value))
        
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
    @discord.app_commands.checks.has_any_role("Administrator")
    async def changerank(self, interaction: discord.Interaction, user: discord.Member, rank:Literal[tuple(ranklist.keys())] , reason: str):
        await interaction.response.defer(ephemeral=True)
        loading = await interaction.followup.send("<a:loading:1424337544891338784> Calling Rover...", ephemeral=True)
        roverResponse = discordToRoblox(rover_token, server_id, user.id)
        response_data = await roverResponse 
        usernameRover = response_data["cachedUsername"]
        userIdRover = response_data["robloxId"]
        group = await client.get_group(2568175)
        userRank = getRankInGroup(userIdRover)
        rankId = ranklist.get(rank)
        await loading.edit(content="<a:loading:1424337544891338784> Determining manipulation type...")
        if userRank > rankId:
            await loading.edit(content="<a:loading:1424337544891338784> Determined as demotion...")
            channel = 1030362797697159240
        else:
            await loading.edit(content="<a:loading:1424337544891338784> Determined as promotion...")
            channel = 1030362796774400040
        channel = interaction.client.get_channel(channel)
        await group.set_rank(userIdRover, ranklist[rank])
        keys = [key for key, val in ranklist.items() if val == userRank]
        await channel.send(view=PromotionMessage(finalString=f"{usernameRover} (<@{user.id}>)\n**{keys[0]} --> {rank}**", user=interaction.user.id, reason=reason))
        await loading.edit(content=":white_check_mark: Rank changed!")

    @app_commands.command(
        name="manipluate-rank-bulk",
        description="Edit lots of users ranks."
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role("Administrator")
    async def changerankbulk(self, interaction: discord.Interaction, rank:Literal[tuple(ranklist.keys())]):
        __import__('pprint').pprint(rank)
        await interaction.response.send_modal(Bulkmanipluate(rank))

async def setup(bot: commands.Bot):
    await bot.add_cog(Rolemanipulations(bot), guild=discord.Object(id=server_id))
