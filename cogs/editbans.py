from discord import app_commands, ui
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

intents = discord.Intents.all()
intents.members = True

load_dotenv()
server_id = os.getenv('SERVER_ID')
herokuapp_token = os.getenv("HEROKUAPP_TOKEN")
roblosecurity = os.getenv("ROBLOSECURITY")

client = Client(roblosecurity)
bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree

async def getBanId(userid):
    recordUrl = f"https://riskuniversalis.herokuapp.com/api/ban/record/{userid}"
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"bearer {herokuapp_token}" 
        }
        async with session.get(recordUrl, headers=headers) as response:
            r = await response.json()
            return r[0]["ban_id"]

class Editbans(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name="edit-ban",
        description="Edit an ingame banishment"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @app_commands.describe(time="Time to edit to (in days)")
    @discord.app_commands.checks.has_any_role("Moderator", "Senior Moderator", "Administrator")
    async def editban(self, interaction: discord.Interaction, user_id: int, time: int, reason: str):
        await interaction.response.defer(thinking=True)
        modifyUrl = "https://riskuniversalis.herokuapp.com/api/ban/modify"
        data = {
                "banId": await getBanId(user_id),
                "reason": reason,
                "duration": time * 86400
        }    
        headers = {
            "Authorization": f"bearer {herokuapp_token}" 
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(modifyUrl, data=data, headers=headers) as response:
                match response.status:
                    case 200:
                        channel = interaction.client.get_channel(1414284581879939072)
                        await channel.send(f"<@{interaction.user.id}> has modified a ban for `{user_id}` to {time} days and reasoned with `{reason}`")
                        await interaction.followup.send(f"Ban for **{user_id}** successfully retimed to {time * 86400} seconds and reasoned with `{reason}`")
                    case 403:
                        await interaction.followup.send(f"403 Forbidden, is user banned?", ephemeral=True)
                    case _:
                        await interaction.followup.send(f"Unknown error: {response.status}", ephemeral=True)


    @app_commands.command(
        name="heroku-unban",
        description="Remove a banishment"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role("Administrator")
    async def rmban(self, interaction: discord.Interaction, user_id: int, reason:str):
        await interaction.response.defer(thinking=True)
        banId = await getBanId(user_id)
        modifyUrl = f"https://riskuniversalis.herokuapp.com/api/ban/revoke?banId={banId}"
        headers = {
            "Authorization": f"bearer {herokuapp_token}" 
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(modifyUrl, headers=headers) as response:
                match response.status:
                    case 200:
                        channel = interaction.client.get_channel(1414284581879939072)
                        group = await client.get_group(2568175)
                        await group.set_rank(user_id, 1)
                        await channel.send(f"<@{interaction.user.id}> has unbanned `{user_id}` reasoned with `{reason}`")
                        await interaction.followup.send(f"Ban for **{user_id}** successfully revoked and reasoned with `{reason}`")
                    case 404:
                        await interaction.followup.send(f"404 not found, is user banned?", ephemeral=True)
                    case _:
                        await interaction.followup.send(f"Unknown error: {response.status}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Editbans(bot), guild=discord.Object(id=server_id))
