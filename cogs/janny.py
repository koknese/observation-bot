import discord
import sqlite3
from discord import app_commands, Embed, ui
from discord.utils import get
from discord.ext import commands
from dotenv import load_dotenv
from typing import Literal
from datetime import datetime, timedelta
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

def lengthStringToSec(string):
    indicator = string[-1]
    number = int(string[:-1])
    allowed_indicators =  {
            "d": 86400,
            "h": 3600,
            "m": 60
    }
    if indicator not in list(allowed_indicators.keys()):
        return "illegal indicator"
    else:
        return number * allowed_indicators[indicator]


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
    c.execute(f"SELECT COUNT (*) FROM riskordlogs WHERE user={user.id} AND type='{action_type}' AND {unix_timestamp - 2592000} < timestamp < {unix_timestamp}") 
    count = c.fetchone()
    return count[0]
    c.close()
    conn.close()

def getLastId():
    # horrid solution!
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute(f"SELECT seq FROM sqlite_sequence WHERE name='riskordlogs'")
    count = c.fetchone()
    return count[0]
    c.close()
    conn.close()

def logAction(user, action_type, admin):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute(f"""CREATE TABLE IF NOT EXISTS riskordlogs (
            caseid INTEGER PRIMARY KEY AUTOINCREMENT,
            user INT NOT NULL,
            type TEXT NOT NULL,
            timestamp INT NOT NULL,
            admin INT NOT NULL
            ) 
          """)

    unix_timestamp = str(int(time.time())) # horrible but works

    c.execute(f"INSERT INTO riskordlogs (user, type, timestamp, admin) VALUES (?, ?, ?, ?)", (user.id, action_type, unix_timestamp, admin.id))
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
        await interaction.response.defer()
        punishment_logs_parsed = interaction.client.get_channel(punishment_logs)
        staff_punishment_logs_parsed = interaction.client.get_channel(staff_punishment_logs)
        logAction(user, "warn", interaction.user)
        action_count = actionCountPast30d(user, "warn")
        last_id = getLastId()

        if action_count >= 2:
            warn_mult = action_count - 1 
            await user.timeout(timedelta(seconds=7200*warn_mult)) ## So essentially, for every warn you get 2 more hours in the slammer
            last_id = getLastId()
            embed = genericEmbed(last_id, "warn", interaction.user, user, reason)
            embed.add_field(
                name=f"User reached 2 or more warns, muted for {warn_mult*7200/3600} hours.",
                value="",
                inline=False,
            )
            await punishment_logs_parsed.send(embed=embed)
            await user.send(embed=embed)
            message = await staff_punishment_logs_parsed.send(embed=embed)
            await message.create_thread(name=f"Case {last_id}")
            await interaction.followup.send(f"Warned and muted for {warn_mult*7200/3600} hours", ephemeral=True)
            return

        embed = genericEmbed(last_id, "warn", interaction.user, user, reason)
        await punishment_logs_parsed.send(embed=embed)
        await user.send(embed=embed)
        message = await staff_punishment_logs_parsed.send(embed=embed)
        await message.create_thread(name=f"Case {last_id}")
        await interaction.response.send_message("Warned", ephemeral=True)

    @app_commands.command(
        name="kick",
        description="Kicks a user"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def kick(self, interaction:discord.Interaction, user:discord.Member, reason:str, length:str):
        punishment_logs_parsed = interaction.client.get_channel(punishment_logs)
        staff_punishment_logs_parsed = interaction.client.get_channel(staff_punishment_logs)
        logAction(user, "kick", interaction.user)
        action_count = actionCountPast30d(user, "kick")
        last_id = getLastId()
        embed = genericEmbed(last_id, "kick", interaction.user, user, reason)
        await punishment_logs_parsed.send(embed=embed)
        await user.send(embed=embed)
        message = await staff_punishment_logs_parsed.send(embed=embed)
        await message.create_thread(name=f"Case {last_id}")
        await interaction.response.send_message(f"Kicked", ephemeral=True)

    @app_commands.command(
        name="mute",
        description="Mute a user"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def mute(self, interaction:discord.Interaction, user:discord.Member, reason:str, length:str):
        if user.is_timed_out():
            await user.timeout(None)
            await interaction.response.send_message("Unmuted")
            embed = genericEmbed(0, "timeout", interaction.user, user, reason)
            embed.add_field(
                name="User unmuted.",
                value="",
                inline=False,
            )
            message = await staff_punishment_logs_parsed.send(embed=embed)
            await message.create_thread(name=message.id)

        length = lengthStringToSec(length)
        punishment_logs_parsed = interaction.client.get_channel(punishment_logs)
        staff_punishment_logs_parsed = interaction.client.get_channel(staff_punishment_logs)
        logAction(user, "timeout", interaction.user)
        action_count = actionCountPast30d(user, "timeout")
        last_id = getLastId()

        if action_count >= 4:
            embed = genericEmbed(last_id, "timeout", interaction.user, user, reason) 
            embed.add_field(
                name="User reached 4 or more mutes, appeal in 7 days.",
                value="",
                inline=False,
            )
            await punishment_logs_parsed.send(embed=embed)
            await user.send("https://discord.gg/CDCgYeE5", embed=embed)
            message = await staff_punishment_logs_parsed.send(embed=embed)
            await message.create_thread(name=f"Case {last_id}")
            await user.ban()
            await interaction.response.send_message(f"Banned for 7 days, user had 4 or more mutes", ephemeral=True)
            return

        embed = genericEmbed(last_id, "timeout", interaction.user, user, reason)
        await punishment_logs_parsed.send(embed=embed)
        await user.send(embed=embed)
        await user.timeout(timedelta(seconds=length)) ## So essentially, for every warn you get 2 more hours in the slammer
        message = await staff_punishment_logs_parsed.send(embed=embed)
        await message.create_thread(name=f"Case {last_id}")
        await interaction.response.send_message(f"Muted for {length/3600} hours", ephemeral=True)

    @app_commands.command(
        name="ban",
        description="Ban a user"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def ban(self, interaction:discord.Interaction, user:discord.Member, reason:str, appealable:bool):
        punishment_logs_parsed = interaction.client.get_channel(punishment_logs)
        staff_punishment_logs_parsed = interaction.client.get_channel(staff_punishment_logs)
        logAction(user, "ban", interaction.user)
        action_count = actionCountPast30d(user, "ban")
        last_id = getLastId()
        if appealable:
            await user.send("https://discord.com/CDCgYeE5", embed=embed)
        else:
            await user.send(embed=embed)

        await user.ban()
        message = await staff_punishment_logs_parsed.send(embed=embed)
        await message.create_thread(name=f"Case {last_id}")
        await interaction.response.send_message(f"Banned", ephemeral=True)
        embed = genericEmbed(last_id, "ban", interaction.user, user, reason)
        await punishment_logs_parsed.send(embed=embed)
        await user.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Janny(bot), guild=discord.Object(id=server_id))
