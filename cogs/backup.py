from dotenv import load_dotenv
import os
import sqlite3
import json
import time
import pprint
import hmac
import hashlib
import requests
import discord
import time
from discord.utils import get
from discord.ext import commands
from discord import app_commands, Embed, ui
from discord.app_commands import Group, command
from discord.ext.commands import GroupCog

load_dotenv("../.env")
fc_secret = os.getenv('API_SECRET')
server_id = os.getenv('SERVER_ID')
fc_api_key = os.getenv('API_KEY')
ha_role = int(os.getenv('HA_ROLE'))
timestamp = int(time.time() * 1000)
hash_bytes = hmac.new(fc_secret.encode(), (fc_api_key + str(timestamp)).encode(), hashlib.sha1).digest()
hash_string = hash_bytes.hex()

class Backup(GroupCog, group_name="backup", group_description="FC backups"):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
    
    @command(
            name="create",
            description="create fc backups"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role(ha_role)
    async def create(self, interaction: discord.Interaction, fc_app_id: str):
        params = {
            "api_key": fc_api_key,
            "hash": hash_string,
            "timestamp": timestamp,
            "project_id": fc_app_id
        }
        url = "https://freedcamp.com/api/v1/tasks"
        response = requests.get(url, params=params)
        if response.status_code == 200:
            await interaction.channel.send(f"-# Got response 200 from Freedcamp API, collecting data... {interaction.user}")
            await interaction.response.defer(thinking=True, ephemeral=True)
            data = response.json()
            conn = sqlite3.connect('backup.db')
            c = conn.cursor()
            c.execute(f"DROP TABLE IF EXISTS {"t" + fc_app_id};")
            c.execute(f"""CREATE TABLE IF NOT EXISTS {"t" + fc_app_id} (
                          name TEXT NOT NULL UNIQUE,
                          description TEXT 
                          )""")
            for task in data["data"]["tasks"]:
                print(f"{task["title"]} : {task["description"].strip()}")
                print(type(task["title"]))
                c.execute(f"INSERT INTO {"t" + fc_app_id} (name, description) VALUES (?, ?);", (task["title"], task["description"],))
            conn.commit()
            c.close()
            conn.close()
            await interaction.followup.send(f"Tasks and their descriptions for board {fc_app_id} collected!")
        else:
            await interaction.response.send_message(f"Got response {response.status_code} from Freedcamp API: `{response.text}`")
            print(f"getId :: {response.text}")

    @app_commands.command(
            name="request",
            description="request the backup database"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role(ha_role)
    async def request(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            db = discord.File("backup.db", filename="backup.db")
            await interaction.followup.send("Database sent", file=db)
        except Exception as e:
            await interaction.followup.send(e)
async def setup(bot: commands.Bot):
    await bot.add_cog(Backup(bot), guild=discord.Object(id=server_id))
