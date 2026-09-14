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
    
@tree.command(name="reload", description="DEBUG: reload a cog", guild=discord.Object(id=server_id))
async def load_cog(interaction: discord.Interaction, extension: str):
    if interaction.user.id == 432437043956809738:
        await bot.reload_extension(f"cogs.{extension}")
        await interaction.response.send_message(f"cog '{extension}' reloaded.")
        await tree.sync(guild=discord.object(id=server_id)) 
        print(f"cog '{extension}' has been reloaded.")
    else:
        await interaction.response.send_message(f"not owner.")

@tree.command(name="force-sync", description="DEBUG: forcesync", guild=discord.Object(id=server_id))
async def forcesync(interaction: discord.Interaction):
    if interaction.user.id == 432437043956809738:
        await interaction.response.send_message("Force sync...")
        await tree.sync(guild=discord.Object(id=server_id))
        print(f"FORCE SYNC.")
    else:
        await interaction.response.send_message(f"not owner.")

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

    cogs = {
        "cogs.observe": "Observations",
        "cogs.backup": "Backup",
        "cogs.modassistance": "Mod assistance",
        "cogs.reports": "Reports",
        # "cogs.staffwarn": "Staff warns", nophono uses this
        "cogs.inactivity": "Inactivity",
        # "cogs.rolemanipulation": "Role manipulations", broken
        "cogs.petition": "Petitions",
        "cogs.jarvis": "Jarvis",
        "cogs.tickets": "Tickets"
    }
    for cog,name in cogs.items():
        await bot.load_extension(cog)
        __import__('pprint').pprint(f"{name} cog has been loaded")
        
    await tree.sync(guild=discord.Object(id=server_id))  # Sync the commands after loading the cog
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"/report for reports"))
    print(discord.__version__)

bot.run(token)
