import discord
import sqlite3
from discord import app_commands, Embed, ui
from discord.utils import get
from discord.ext import commands
from dotenv import load_dotenv
from typing import Literal
from datetime import datetime
import os
import time 

intents = discord.Intents.all()
intents.members = True

load_dotenv("../.env")
server_id = os.getenv('SERVER_ID')
punishment_logs = int(os.getenv('PUNISHMENT_LOGS'))
staff_punishment_logs = int(os.getenv('STAFF_PUNISHMENT_LOGS'))

# Action types
# warn
# timeout
# ban
# mute

def genericEmbed(caseid, action_type, author, target, reason):
    embed = discord.Embed(
        color=16038116,
        description="-# DM sent",
        timestamp=datetime.now(),
    )
    embed.set_author(
        name=f"Case {caseid} ({action_type})",
        icon_url=f"https://github.com/allthingslinux/tux/blob/main/assets/emojis/{action_type}.png?raw=true", # we LOOOOOOOOOVE stealing assets <3
    )
    embed.set_footer(
        text="janny@risky #",
    )
    embed.add_field(
        name="Moderator",
        value=f"-# **{author}** `{author.id}`",
        inline=True,
    )
    embed.add_field(
        name="Target",
        value=f"-# **{target}** `{target.id}`",
        inline=True,
    )
    embed.add_field(
        name="Reason",
        value=f"> -# {reason}",
        inline=False,
    )
    return embed

def actionCountPast30d(user, action_type):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    unix_timestamp = int(time.time()) # horrible but works
    c.execute(f"SELECT COUNT (*) FROM riskordlogs WHERE user={user.id} AND action_type={action_type} AND {unix_timestamp - 2592000} < timestamp < {unix_timestamp}") 
    count = c.fetchone()
    __import__('pprint').pprint(count)
    return count[0]
    c.close()
    conn.close()

def getLastId():
    # horrid solution!
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute(f"SELECT seq FROM sqlite_sequence WHERE name='riskordlogs'")
    count = c.fetchone()
    __import__('pprint').pprint(count)
    return count[0]
    c.close()
    conn.close()

def logAction(user, action_type):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute(f"""CREATE TABLE IF NOT EXISTS riskordlogs (
            caseid INTEGER PRIMARY KEY AUTOINCREMENT,
            user INT NOT NULL,
            type TEXT NOT NULL,
            timestamp INT NOT NULL
            ) 
          """)

    unix_timestamp = str(int(time.time())) # horrible but works

    c.execute(f"INSERT INTO riskordlogs (user, type, timestamp) VALUES (?, ?, ?)", (user.id, action_type, unix_timestamp))
    conn.commit()
    c.close()
    conn.close()

class Janny(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name="warn",
        description="Warn a user"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def warn(self, interaction:discord.Interaction, user:discord.Member, reason:str):
        punishment_logs_parsed = interaction.client.get_channel(punishment_logs)
        staff_punishment_logs_parsed = interaction.client.get_channel(staff_punishment_logs)
        logAction(user, "warn")
        __import__('pprint').pprint(actionCountPast30d(user, "warn"))
        last_id = getLastId()
        embed = genericEmbed(last_id, "warn", interaction.user, user, reason)
        await punishment_logs_parsed.send(embed=embed)
        await user.send(embed=embed)
        message = await staff_punishment_logs_parsed.send(embed=embed)
        await message.create_thread(name=f"Case {last_id}")
        await interaction.response.send_message("Warned", ephemeral=True)

    #@app_commands.command(
    #    name="mute",
    #    description="Warn a user"
    #)
    #@app_commands.guilds(discord.Object(id=server_id))
    #@app_commands.describe(proof="Image formats !!ONLY!!")
    #async def warn(self, interaction:discord.Interaction, user:discord.Member, reason:str, proof:discord.Attachment):
    #    punishment_logs = bot.get_channel(punishment_logs)
    #    logAction(user, "warn")
    #    embed = genericEmbed(getLastId(), "warn", interaction.user, user, reason)
    #    await punishment_logs.send(embed=embed)
    #    await 

async def setup(bot: commands.Bot):
    await bot.add_cog(Janny(bot), guild=discord.Object(id=server_id))
