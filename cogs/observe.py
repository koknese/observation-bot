from misc.rover import robloxToDiscord
from discord import app_commands, Embed, ui
from discord.utils import get
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
from typing import Literal  
import os
import time 
import pprint
import discord
import hmac
import hashlib
import requests
import sqlite3

intents = discord.Intents.all()
intents.members = True

def getUserId(username):
    requestPayload = {
            "usernames": [
                username
            ],
            "excludeBannedUsers": True # Whether to include banned users within the request, change this as you wish
           }
        
    responseData = requests.post(ID_API_ENDPOINT, json=requestPayload)
        
            # Make sure the request succeeded
    assert responseData.status_code == 200
        
    userId = responseData.json()["data"][0]["id"]
        
    print(f"getUserId :: Fetched user ID of username {username} -> {userId}")
    return userId

load_dotenv()
server_id = os.getenv('SERVER_ID')
fc_secret = os.getenv('API_SECRET')
rover_token = os.getenv('ROVER_KEY')
fc_api_key = os.getenv('API_KEY')

mod_id = os.getenv('MOD_ID')
sm_id = os.getenv('SM_ID')
gm_id = os.getenv('GM_ID')
tm_id = os.getenv('TM_ID')

observation_access = int(os.getenv('OBS_ROLE'))
stats_access = int(os.getenv('HA_ROLE'))

timestamp = int(time.time() * 1000)  
hash_bytes = hmac.new(fc_secret.encode(), (fc_api_key + str(timestamp)).encode(), hashlib.sha1).digest()
hash_string = hash_bytes.hex()

bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree

def getId(username, app_id):
    params = {
        "api_key": fc_api_key,
        "hash": hash_string,
        "timestamp": timestamp,
        "project_id": app_id
    }
    url = "https://freedcamp.com/api/v1/tasks"
    response = requests.get(url, params=params)
    if response.status_code == 200:
        r = response.json()

        pprint.pprint(r)
    
        def getTaskByTitle():
            for task in r["data"]["tasks"]:
                if task["title"] == username:
                    print(f"TASK: {task}")
                    return task
            return None

        if getTaskByTitle():
            print(f"ID: {getTaskByTitle()["id"]}")
            return getTaskByTitle()["id"]
        else:
            return None
    else:
        print(f"getId :: {response.text}")

def postComment(task_id, contents, api_key, hash_string, app_id):
    url = f"https://freedcamp.com/api/v1/comments"
    params = {
        "api_key": api_key,
        "hash": hash_string,
        "timestamp": timestamp
    }
    data = {
        "description": contents,
        "app_id": app_id,
        "task_id": task_id
    }

    response = requests.post(url, json=data, params=params)

    if response.status_code == 200:
        r = response.json()
    else:
        print(f"postComment:: {response.text}")


class Observation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name='observe',
        description='Submit an observation of a staff member'
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @app_commands.describe(roblox_username="User to log an observation for.")
    @discord.app_commands.checks.has_any_role(observation_access)
    async def observe(self, interaction: discord.Interaction, roblox_username: str, observation_type: Literal["Positive", "Negative"], description: str, rank: Literal["Gamemaster", "Trial Moderator", "Moderator", "Senior Moderator"], evidence: discord.Attachment = None):
      
        current_month = datetime.now().month
        current_year = datetime.now().year
        def determineEmbedColor():
          if observation_type == "Positive":
            return discord.Color.green()
          elif observation_type == "Negative":
            return discord.Color.red()
    
        def determineSpanColor():
          if observation_type == "Positive":
              color = "008000"
              return color
          elif observation_type == "Negative":
              color = "c0392b"
              return color

        def correctRankId(chosenRank):
            match chosenRank:
                case "Gamemaster":
                    return gm_id
                case "Trial Moderator":
                    return tm_id
                case "Moderator":
                    return mod_id
                case "Senior Moderator":
                    return sm_id

        def replaceEvidence():
            if evidence:
                return evidence.url
            else:
                image = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ft7.rbxcdn.com%2F180DAY-2a5fb6516cb2af0716dd4232c8928f8c&f=1&nofb=1&ipt=9058510af8dcc181d59a9f64b649de28a9cc877cdafa57a63243ce3542b5dd72"
                return image
        
        embedcolor = determineEmbedColor()
        
        class Buttons(discord.ui.View):
            def __init__(self, *, timeout=180):
                super().__init__(timeout=timeout)
    
            @discord.ui.button(label="I've verified that the info is correct", style=discord.ButtonStyle.green)
            async def accept_application(self, interaction: discord.Interaction, view: discord.ui.View):
                try:
                    await interaction.response.defer(thinking=True)
                    comment = f"""
                                <h2>
                                    <span style="color: #{determineSpanColor()}">
                                        <strong>{observation_type}</strong>
                                    </span> 
                                    - Logged by {interaction.user}({interaction.user.id}) 
                                    <a href="{replaceEvidence()}">(provided proof)</a>
                                </h2>
                                
                                <blockquote>
                                    {description}
                                </blockquote>
                                """.strip()
    
                    postComment(getId(roblox_username, correctRankId(rank)), comment, fc_api_key, hash_string, correctRankId(rank))
    
                    embed.set_footer(text="Abuse will lead to harsh punishment!")
                    await interaction.followup.send(embed=embed)

                    conn = sqlite3.connect("data.db")
                    c = conn.cursor()
                    tableName = "o" + str(interaction.user.id) # bypassing sqlite not allowing numbers as table names
                    c.execute(f"""CREATE TABLE IF NOT EXISTS {tableName}(
                                short_date TEXT NOT NULL,
                                timestamp TEXT NOT NULL
                                ) 
                              """)

                    shortDate = str(current_month) + "." + str(current_year)
                    unix_timestamp = str(int(time.time())) # horrible but works

                    c.execute(f"INSERT INTO {tableName} (short_date, timestamp) VALUES (?, ?)", (shortDate, unix_timestamp))
                    conn.commit()
                    c.close()
                    conn.close()

                    # dming part
                    user = interaction.client.get_user(int(robloxToDiscord(rover_token, server_id, getUserId(roblox_username))["discordUsers"][0]["user"]["id"])) # roblox username to discord id
                    embed.set_author(name=f"You have received a {observation_type.lower()} observation!", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse2.mm.bing.net%2Fth%3Fid%3DOIP.sUVyywAHU0Q2V2hyo_dligAAAA%26pid%3DApi&f=1&ipt=d3f8072407cd9ca31c41b0ab08fa9104c7b3292fdb636a5d6d6e37c0591af2c8&ipo=images")
                    embed.set_footer(text="For any questions or concerns, go to the staff-meeting channel in Staff Hub.")
                    await user.send("# ATTENTION!", embed=embed)
                except Exception as e:
                    await interaction.channel.send(f"An error has occured:\n```{e}```")
    
        embed = discord.Embed(title=f'Observing {roblox_username}', color=embedcolor)
        embed.set_author(name=f"Logged by {interaction.user}", icon_url=str(interaction.user.avatar))
        embed.set_thumbnail(url=replaceEvidence())
        embed.add_field(name="Description", value=description, inline=True)
        embed.set_footer(text="This is a preview. Click the button below to send submit the observation. Resend the command with correct information if you've made a mistake.")
        await interaction.response.send_message(embed=embed, view=Buttons(), ephemeral=True)

    @app_commands.command(
        name='observation-stats',
        description='View the amount of observations made by a specific staff member'
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role(observation_access)
    async def stats(self, interaction: discord.Interaction, user: discord.Member):
        current_month = datetime.now().month
        current_year = datetime.now().year
        try:
            class Droptable(discord.ui.View):
                def __init__(self, *, timeout=40, userid):
                    super().__init__(timeout=timeout)

            shortDateNow = str(current_month) + "." + str(current_year)
            shortDateLastMonth = str(current_month - 1) + "." + str(current_year)
            tableName = "o" + str(user.id)
            conn = sqlite3.connect('data.db')
            c = conn.cursor()

            queries = [
                f"SELECT COUNT (*) FROM {tableName} WHERE short_date = {shortDateNow}", # gets the obs for current month
                f"SELECT COUNT (*) FROM {tableName} WHERE short_date = {shortDateLastMonth}", # gets the obs for last month
                f"SELECT COUNT (*) FROM {tableName}" # gets the obs for all time
            ]

            def execute_many_selects(cursor, queries):
                return [cursor.execute(query).fetchone()[0] for query in queries]

            results = execute_many_selects(c, queries)

            embed = discord.Embed(title=f"{user}'s logged observations",
                      colour=0x813d9c)

            embed.set_author(name=f"{user} ({user.id})",
                             icon_url=user.avatar.url)
            
            embed.add_field(name="Observations made last month",
                            value=results[1],
                            inline=False)
            embed.add_field(name="Observations made this month",
                            value=results[0],
                            inline=False)
            embed.add_field(name="Total observations",
                            value=results[2],
                            inline=True)
            
            embed.set_footer(text=f"invoked by {interaction.user}",
                             icon_url=interaction.user.avatar.url)

            await interaction.response.send_message(embed=embed, ephemeral=True, view=Droptable(userid=user.id))
        except Exception as e:
            await interaction.channel.send(e)

    @app_commands.command(
        name='drop-obs-table',
        description='Wipe the observation log for an admin'
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @app_commands.describe(user="!!THIS ACTION IS IRREVERSIBLE!! The admin to get his observation stats wiped.")
    @discord.app_commands.checks.has_any_role(stats_access)
    async def drop_table(self, interaction: discord.Interaction, user: discord.Member):
        try:
            embed = discord.Embed(title=f"All data has been irreversibly deleted.",
                description=f"# :warning: TABLE FOR <@{user.id}> DROPPED! \n### This incident will be reported.",
                colour=0xe01b24)

            embed.set_author(name=f"Table dropped by {interaction.user}",
            icon_url=interaction.user.avatar)

            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            c.execute(f"DROP TABLE {"o" + str(user.id)}")
            pprint.pprint(f"{interaction.user} has dropped table {user.id}")
            await interaction.response.send_message(embed=embed)
            conn.commit()
            c.close()
            conn.close()
        except Exception as e:
            await interaction.channel.send(e)

async def setup(bot: commands.Bot):
    await bot.add_cog(Observation(bot), guild=discord.Object(id=server_id))
