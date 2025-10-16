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
#@discord.app_commands.checks.has_permissions(administrator=True)
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
#@discord.app_commands.checks.has_permissions(administrator=True)
async def load_cog(interaction: discord.Interaction, extension: str):
    if interaction.user.id == 432437043956809738:
        await bot.unload_extension(f"cogs.{extension}")
        await interaction.response.send_message(f"Cog '{extension}' unloaded.")
        await tree.sync(guild=discord.Object(id=server_id)) 
        print(f"Cog '{extension}' has been unloaded.")
    else:
        await interaction.response.send_message(f"Not owner.")

@tree.command(name="nuke", description="RiskordNuker1000", guild=discord.Object(id=server_id))
#@discord.app_commands.checks.has_permissions(administrator=True)
async def load_cog(interaction: discord.Interaction):
    if interaction.user.id == 432437043956:
        await interaction.response.send_message("✅ Nuker rigged to set off <t:1761421140:R>")
    else:
        await interaction.response.send_message("Not owner")
    
    
@tree.command(name="force-sync", description="DEBUG: forcesync", guild=discord.Object(id=server_id))
@discord.app_commands.checks.has_permissions(administrator=True)
async def forcesync(interaction: discord.Interaction):
    await interaction.response.send_message("Force sync...")
    await tree.sync(guild=discord.Object(id=server_id)) 
    print(f"FORCE SYNC.")

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
        
    await tree.sync(guild=discord.Object(id=server_id))  # Sync the commands after loading the cog
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"/report for reports"))
    print(discord.__version__)

bot.run(token)
