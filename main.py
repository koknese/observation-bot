import discord
import json
from discord import app_commands
from discord.utils import get, format_dt
from discord.ext import commands
from dotenv import load_dotenv
from typing import Literal
import os
from datetime import datetime
intents = discord.Intents.all()
intents.members = True

load_dotenv('.env', override=True)
server_id = os.getenv('SERVER_ID').strip()
token = os.getenv('TOKEN')

bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree

@tree.command(name="load", description="DEBUG: load a cog", guild=discord.Object(id=server_id))
async def load_cog(interaction: discord.Interaction, extension: str):
    if interaction.user.id == 432437043956809738:
        await bot.load_extension(f"cogs.{extension}")
        await interaction.response.send_message(f"Cog '{extension}' loaded.")
        await tree.sync(guild=discord.Object(id=server_id)) 
        print(f"Cog '{extension}' has been loaded.")
    else:
        await interaction.response.send_message(f"Not owner.")

@tree.command(name="ping", description="DEBUG: ping", guild=discord.Object(id=server_id))
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Ponged back @ {bot.latency * 1000}ms", ephemeral=True)
    
@tree.command(name="unload", description="DEBUG: unload a cog", guild=discord.Object(id=server_id))
async def load_cog(interaction: discord.Interaction, extension: str):
    if interaction.user.id == 432437043956809738:
        await bot.unload_extension(f"cogs.{extension}")
        await interaction.response.send_message(f"cog '{extension}' unloaded.")
        await tree.sync(guild=discord.object(id=server_id)) 
        print(f"cog '{extension}' has been unloaded.")
    else:
        await interaction.response.send_message(f"not owner.")

@tree.command(name="force-sync", description="DEBUG: forcesync", guild=discord.Object(id=server_id))
@discord.app_commands.checks.has_permissions(administrator=True)
async def forcesync(interaction: discord.Interaction):
    if interaction.user.id == 432437043956809738:
        await interaction.response.send_message("Force sync...")
        await tree.sync(guild=discord.Object(id=server_id))
        print(f"FORCE SYNC.")
    else:
        await interaction.response.send_message(f"not owner.")

@tree.command(name="latex", description="DEBUG: Like ping but more advanced because saltbear is a bum", guild=discord.Object(id=server_id))
async def latex(interaction: discord.Interaction, equation:str):

    #fetch("https://e1kf0882p7.execute-api.us-east-1.amazonaws.com/default/latex2image", {
    #  "headers": {
    #    "accept": "application/json, text/javascript, */*; q=0.01",
    #    "accept-language": "lv-LV,lv;q=0.9",
    #    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    #    "priority": "u=1, i",
    #    "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    #    "sec-ch-ua-mobile": "?0",
    #    "sec-ch-ua-platform": "\"Linux\"",
    #    "sec-fetch-dest": "empty",
    #    "sec-fetch-mode": "cors",
    #    "sec-fetch-site": "cross-site"
    #  },
    #  "referrer": "https://latex2image.joeraut.com/",
    #  "body": "{\"latexInput\":\"\\\\begin{align*}\\nx^2\\n\\\\end{align*}\\n\",\"outputFormat\":\"PNG\",\"outputScale\":\"500%\"}",
    #  "method": "POST",
    #  "mode": "cors",
    #  "credentials": "omit"
    #});
     
    url = "https://e1kf0882p7.execute-api.us-east-1.amazonaws.com/default/latex2image"
    payload = {
        "latexInput": f"\\\\begin{{align*}} {equation} \\\\end{{align*}}",
        "outputFormat": "PNG",
        "outputScale": "500%"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as response:
            res = await response.json()
            if res["error"] == None:
                await interaction.response.send_message(res["imageUrl"])
            else:
                await interaction.response.send_message("Invalid input")

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

    await bot.load_extension("cogs.observe")
    print("Obs cog loaded!")

    await bot.load_extension("cogs.backup")
    print("Backup cog loaded!")

    await bot.load_extension("cogs.modassistance")
    print("Mod assistance cog loaded!")

    await bot.load_extension("cogs.reports")
    print("Reports cog loaded!")

    await bot.load_extension("cogs.staffwarn")
    print("Staff warns cog loaded!")

    await bot.load_extension("cogs.inactivity")
    print("Inactivity cog loaded!")

    await bot.load_extension("cogs.rolemanipulation")
    print("Role manipulations cog loaded!")

    await bot.load_extension("cogs.petition")
    print("Petitions cog loaded!")
        
    await tree.sync(guild=discord.Object(id=server_id))  # Sync the commands after loading the cog
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"/report for reports"))
    print(discord.__version__)

bot.run(token)
