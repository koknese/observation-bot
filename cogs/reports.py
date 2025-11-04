from discord import app_commands, ui
from roblox import Client
from discord.utils import get
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
from typing import Literal  
from misc.rover import discordToRoblox
import os
import time 
import pprint
import discord
import json
import aiohttp

intents = discord.Intents.all()
intents.members = True

load_dotenv()
server_id = os.getenv('SERVER_ID')
rover_token = os.getenv('ROVER_KEY')
herokuapp_token = os.getenv("HEROKUAPP_TOKEN")
roblosecurity = os.getenv("ROBLOSECURITY")
banishment_logs = int(os.getenv("BANISHMENT_LOGS"))
admin = int(os.getenv("OBS_ROLE"))
senior_mod = int(os.getenv("SM_ROLE"))
reports_channel = int(os.getenv("REPORTS_CHANNEL"))

client = Client(roblosecurity)
bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree

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

async def postBan(user, reason, logsLink, expiresIn):
    url = "https://staff.riskuniversalis.org/api/bans/post-ban"
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


class Reasonmodal(discord.ui.Modal, title='Reason'):
    def __init__(self, message, user, length):
        super().__init__()
        self.message = message 
        self.user = user
        self.length = length

    body = ui.TextInput(label='Reason', placeholder="Griefing, nation ruining, powerplay, godplay, abusing !staffGodRolls", style=discord.TextStyle.long)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        unix_timestamp = int(time.time()) # horrible but works
        ban = await postBan(self.user, self.body.value, f"https://discord.com/channels/252552812427214849/{interaction.channel.id}/{self.message.id}", unix_timestamp + self.length)
        __import__('pprint').pprint(ban)
        if ban == 201:
            banlogs = interaction.client.get_channel(banishment_logs)
            roblox_username = await discordToRoblox(rover_token, 252552812427214849, interaction.user.id)
            await banlogs.send(f"{self.user}\n**Banned by**: {roblox_username["cachedUsername"]} (<@{interaction.user.id}>)\n**Length**: until <t:{unix_timestamp + self.length}:f>\n**Reason**: {self.body.value}", embed=self.message.embeds[0])
        else:
            await interaction.followup.send("Something has gone wrong. Does the user exist or is the user already banned?")

class AcceptUi(discord.ui.View):
    def __init__(self, message, user, originalInteraction, *, timeout=None):
        super().__init__(timeout=timeout)
        self.message = message 
        self.user = user
        self.originalInteraction = originalInteraction

    @discord.ui.button(label="Ignore",style=discord.ButtonStyle.gray)
    async def ignore(self, interaction:discord.Interaction,button:discord.ui.Button):
        role = interaction.guild.get_role(senior_mod)
        role2 = interaction.guild.get_role(admin)
        if role not in interaction.user.roles and role2 not in interaction.user.roles:
            await interaction.response.send_message("https://i.kym-cdn.com/photos/images/newsfeed/002/916/147/ec1.jpg", ephemeral=True)
            return
        await interaction.response.send_message(f"Appeal ignored by {interaction.user}.")
        await self.message.edit(content=f"Ignored by <@{interaction.user.id}>", view=None)

    @discord.ui.button(label="3 days",style=discord.ButtonStyle.primary)
    async def three_days(self, interaction:discord.Interaction,button:discord.ui.Button):
        role = interaction.guild.get_role(senior_mod)
        role2 = interaction.guild.get_role(admin)
        if role not in interaction.user.roles and role2 not in interaction.user.roles:
            await interaction.response.send_message("https://i.kym-cdn.com/photos/images/newsfeed/002/916/147/ec1.jpg", ephemeral=True)
            return
        await interaction.response.send_modal(Reasonmodal(self.message, self.user, 259200))
        await self.message.edit(view=None)
        await self.message.edit(content=f"Banned for 3 days by <@{interaction.user.id}>", view=None)

    @discord.ui.button(label="7 days",style=discord.ButtonStyle.primary)
    async def week(self, interaction:discord.Interaction,button:discord.ui.Button):
        role = interaction.guild.get_role(senior_mod)
        role2 = interaction.guild.get_role(admin)
        if role not in interaction.user.roles and role2 not in interaction.user.roles:
            return
        await interaction.response.send_modal(Reasonmodal(self.message, self.user, 604800))
        await self.message.edit(content=f"Banned for 7 days by <@{interaction.user.id}>", view=None)

    @discord.ui.button(label="30 days",style=discord.ButtonStyle.primary)
    async def month(self, interaction:discord.Interaction,button:discord.ui.Button):
        role = interaction.guild.get_role(senior_mod)
        role2 = interaction.guild.get_role(admin)
        if role not in interaction.user.roles and role2 not in interaction.user.roles:
            await interaction.response.send_message("https://i.kym-cdn.com/photos/images/newsfeed/002/916/147/ec1.jpg", ephemeral=True)
            return
        await interaction.response.send_modal(Reasonmodal(self.message, self.user, 2592000))
        await self.message.edit(content=f"Banned for 30 days by <@{interaction.user.id}>", view=None)

    @discord.ui.button(label="6 months",style=discord.ButtonStyle.danger)
    async def half_a_year(self, interaction:discord.Interaction,button:discord.ui.Button):
        role = interaction.guild.get_role(senior_mod)
        role2 = interaction.guild.get_role(admin)
        if role not in interaction.user.roles and role2 not in interaction.user.roles:
            await interaction.response.send_message("https://i.kym-cdn.com/photos/images/newsfeed/002/916/147/ec1.jpg", ephemeral=True)
            return
        await interaction.response.send_modal(Reasonmodal(self.message, self.user, 15638400))
        await self.message.edit(content=f"Banned for 6 months by <@{interaction.user.id}>", view=None)

class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name="report",
        description="Report"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @app_commands.describe(user="Username of the person to report")
    async def reports(self, interaction: discord.Interaction, user: str, reason: str, image: discord.Attachment):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title="Incoming game report",
                      colour=0xf5ed00)

        embed.add_field(name="Reporter",
                        value=f"<@{interaction.user.id}>",
                        inline=False)
        embed.add_field(name="Accused",
                        value=user,
                        inline=False)
        embed.add_field(name="Reasoning",
                        value=reason,
                        inline=False)
        
        embed.set_image(url=image.url)
        reports = interaction.client.get_channel(reports_channel)
        message = await reports.send(embed=embed)
        view = AcceptUi(message, user, interaction)
        await message.edit(embed=embed,view=view)
        await interaction.followup.send("Reported!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Reports(bot), guild=discord.Object(id=server_id))
