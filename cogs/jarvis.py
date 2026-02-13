import discord
import io
import chat_exporter
import requests
import sqlite3
import datetime
from misc.rover import discordToRoblox
from discord import app_commands, Embed, ui
from discord.utils import get
from discord.ext import commands
from dotenv import load_dotenv
from typing import Literal
import os
import pprint

intents = discord.Intents.all()
intents.members = True

ID_API_ENDPOINT = "https://users.roblox.com/v1/usernames/users"
load_dotenv("../.env")
server_id = os.getenv('SERVER_ID')
rover_token = os.getenv('ROVER_KEY')
senior_mod = int(os.getenv("SM_ROLE"))
admin = int(os.getenv("OBS_ROLE"))
herokuapp_token = os.getenv("HEROKUAPP_TOKEN")
banishment_logs = int(os.getenv("BANISHMENT_LOGS"))

def getHeadshot(userId):
    userRawHeadshot = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={userId}&format=png&size=352x352"
    response = requests.get(userRawHeadshot)
    if response.status_code == 200:
        userParsedHeadshot = response.json()
        userFinalHeadshot = userParsedHeadshot['data'][0]['imageUrl']
        print(f"getHeadshot :: Fetched headshot of {userId}")
        return userFinalHeadshot
    else:
        placeholderImg = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fi.imgflip.com%2Fd0tb7.jpg&f=1&nofb=1&ipt=e1c23bf6c418254a56c19b09cc9ece6238ead393652e54278f0d535f9fb81c56"
        return placeholderImg

#time = datetime.datetime.now()
def getGreeting(time):
    current_time = time.strftime('%H:%M:%S')  # Current Time in HH:MM:SS Format
    current_hour = int(time.strftime('%H'))  # Extracting the Hour Part
    current_day = time.strftime('%A')  # Extracting the Hour Part
    print(f"Current time: {current_time}")  # Display the Current Time
    print(current_day)

    if str(current_day) == "Friday":
        return "Happy Friday"
    elif current_hour < 12:
        return "Good Morning"
    elif current_hour < 16:
        return "Good Afternoon"
    elif current_hour < 20:
        return "Good Evening"
    else:
        return "Good Night"

async def postBan(user, reason, logsLink, expiresIn, bannedBy):
    url = f"https://staff.riskuniversalis.org/api/bans/post-ban-proxy/{bannedBy}"
    headers = {
        'Cookie': f"sessionToken={herokuapp_token}"
    }
    # {user: "123123sad", reason: "s", logsLink: "s", expiresIn: 1762902579, appealable: true}
    payload = {
        "user": user,
        "reason": reason,
        "logsLink": logsLink,
        "expiresIn": expiresIn,
        "appealable": True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=headers) as response:
            __import__('pprint').pprint(response.status)
            res = await response.json()
            __import__('pprint').pprint(res)
            return response.status

async def deleteBan(user):
    url = f"https://staff.riskuniversalis.org/api/bans/delete-ban/{user}"
    headers = {
        'Cookie': f"sessionToken={herokuapp_token}"
    }
    # {user: "123123sad", reason: "s", logsLink: "s", expiresIn: 1762902579, appealable: true}
    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=headers) as response:
            __import__('pprint').pprint(response.status)
            res = await response.json()
            __import__('pprint').pprint(res)
            return response.status

class Ban(discord.ui.Modal, title='Banning a player'):
    def __init__(self,roblox_username):
        self.roblox_username = roblox_username
        super().__init__()

    user = ui.TextInput(label='User to ban', placeholder="saltbear1", style=discord.TextStyle.short)
    reason = ui.TextInput(label='Reason', placeholder="Freepaint", style=discord.TextStyle.short)
    length = ui.TextInput(label='Length', placeholder="7d, 14d, Permanent, etc.", style=discord.TextStyle.short)
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.length.value[-1].lower() == "d":
            finalLength = self.length.value[:-1] * 86400
        elif self.length.value.lower() == "permanent":
            finalLength = None
        else:
            await interaction.response.send_message("Malformed length", ephemeral=True)
            return
    
        ban = await postBan(self.user.value, self.reason.value, )
        __import__('pprint').pprint(ban)
        if ban == 201:
            banlogs = interaction.client.get_channel(banishment_logs)
            await banlogs.send(f"{self.user}\n**Banned by**: {self.roblox_username}\n**Length**: until <t:{unix_timestamp + self.length}:f>\n**Reason**: {self.body.value}")
        else:
            await interaction.response.send_message("Something has gone wrong. Does the user exist or is the user already banned?")

class Unban(discord.ui.Modal, title='Unbanning a player'):
    def __init__(self,):
        super().__init__()

    user = ui.TextInput(label='User to unban', placeholder="nuumnuum", style=discord.TextStyle.short)
    
    async def on_submit(self, interaction: discord.Interaction):
        ban = await deleteBan(self.user.value)
        __import__('pprint').pprint(ban)
        if ban == 201:
            banlogs = interaction.client.get_channel(banishment_logs)
            await banlogs.send(f"{self.user}\n**Banned by**: {roblox_username["cachedUsername"]} (<@{interaction.user.id}>)\n**Length**: until <t:{unix_timestamp + self.length}:f>\n**Reason**: {self.body.value}", embed=self.message.embeds[0])
        else:
            await interaction.response.send_message("Something has gone wrong. Does the user exist or is the user already banned?")

class Actions(ui.ActionRow):
    def __init__(self, view: 'Actions') -> None:
        self.__view = view
        super().__init__()

    @ui.button(label='Ban a player', style=discord.ButtonStyle.red, emoji="<:banUser:1471189951516250243>")
    async def new_image(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(Ban)

    @ui.button(label='Unban a player', style=discord.ButtonStyle.primary, emoji="<:unbanUser:1471211707190870311>")
    async def change_text(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(ChangeTextModal(self.__view))

class Welcome(ui.LayoutView):
    def __init__(self, *, roblox_user:str, roblox_id:int, greeting:str) -> None:
        super().__init__(timeout=None)
        self.roblox_id = roblox_id
        self.roblox_user = roblox_user
        self.greeting = greeting

        self.thumbnail = ui.Thumbnail(media=getHeadshot(self.roblox_id))
        self.title = ui.TextDisplay(f"## <:logged:1471188673893765356> Welcome to Jarvis:tm:\n{self.greeting}, **{self.roblox_user}.**")

        self.separator = ui.Separator(visible=True)
        self.section = ui.Section(self.title, accessory=self.thumbnail)

        container = ui.Container(
            self.thumbnail,
            self.section,
            self.separator,
        )
        self.add_item(container)

class Jarvis(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name="jarvis",
        description="Access RiskAPI via Risky"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def jarvis(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(senior_mod)
        role2 = interaction.guild.get_role(admin)
        if role not in interaction.user.roles and role2 not in interaction.user.roles:
            return   
        await interaction.response.defer()
        await interaction.followup.send("Logging in...", ephemeral=True)
        rover_data = await discordToRoblox(rover_token, 252552812427214849, interaction.user.id)
        await interaction.followup.send(view=Welcome(roblox_user=rover_data["cachedUsername"], roblox_id=int(rover_data["robloxId"]), greeting=getGreeting(datetime.datetime.now())))
    # def __init__(self, *, roblox_user:str, roblox_id:int, roblox_portrait:str, greeting:str, interaction:any) -> None:

async def setup(bot: commands.Bot):
    await bot.add_cog(Jarvis(bot), guild=discord.Object(id=server_id))
