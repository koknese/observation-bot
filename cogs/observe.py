from misc.rover import robloxToDiscord
from misc.imgbb import upload
from misc.paginator import Pagination
from discord import app_commands, ui
from discord.utils import get
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
from typing import Literal  
import calendar
import os
import asyncio
import time 
import pprint
import discord
import json
import hmac
import hashlib
import requests
import sqlite3

intents = discord.Intents.all()
intents.members = True
ID_API_ENDPOINT = "https://users.roblox.com/v1/usernames/users"

load_dotenv()
server_id = os.getenv('SERVER_ID')
fc_secret = os.getenv('API_SECRET')
rover_token = os.getenv('ROVER_KEY')
fc_api_key = os.getenv('API_KEY')
logging_channel_id = int(os.getenv("LOGGING_CHANNEL"))
imgbb_key = os.getenv("IMGBB_KEY")
deletion_log = int(os.getenv("DELETION_LOGS"))

mod_id = os.getenv('MOD_ID')
sm_id = os.getenv('SM_ID')
gm_id = os.getenv('GM_ID')
tm_id = os.getenv('TM_ID')

observation_access = int(os.getenv('OBS_ROLE'))
stats_access = int(os.getenv('HA_ROLE'))

bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree

def getUserId(username, interaction = None):
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

def getRankInGroup(userid):
    if userid:
        request = requests.get(f"https://groups.roblox.com/v1/users/{userid}/groups/roles")
        response = json.loads(request.text)
        for i in response["data"]:
            if i["group"]["id"] == 2568175:
                return i["role"]["name"]
    else:
        error = "User ID couldn't be found or user not in group."
        return error

def getId(username, app_id):
    timestamp = int(time.time() * 1000)  
    hash_bytes = hmac.new(fc_secret.encode(), (fc_api_key + str(timestamp)).encode(), hashlib.sha1).digest()
    hash_string = hash_bytes.hex()
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
    
        def getTaskByTitle():
            for task in r["data"]["tasks"]:
                if task["title"].lower() == username.lower(): # using .lower in order to bypass case sensitivity 
                    print(f"TASK FOUND")
                    return task
            return None

        if getTaskByTitle():
            print(f"ID: {getTaskByTitle()["id"]}")
            return getTaskByTitle()["id"]
        else:
            return None
    else:
        print(f"getId :: {response.text}")

def postComment(task_id, contents, api_key, app_id):
    timestamp = int(time.time() * 1000)  
    hash_bytes = hmac.new(fc_secret.encode(), (fc_api_key + str(timestamp)).encode(), hashlib.sha1).digest()
    hash_string = hash_bytes.hex()
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
    @app_commands.describe(roblox_username="User to log an observation for.", description="Use `\\n` to make a new line, for example \"Hello\\nHello on a new line!\"", count_towards_quota="If false, this won't log into your observation stats.", primary_evidence="To add more images, you must have primary_evidence uploaded. This will also be seen in FC.")
    @discord.app_commands.checks.has_any_role(observation_access)
    async def observe(self, interaction: discord.Interaction, roblox_username: str, observation_type: Literal["Positive", "Negative", "Neutral", "Information"], description: str, count_towards_quota: bool, primary_evidence: discord.Attachment , evidence2: discord.Attachment = None, evidence3: discord.Attachment = None, evidence4: discord.Attachment = None, evidence5: discord.Attachment = None, evidence6: discord.Attachment = None, evidence7: discord.Attachment = None,):
        if interaction.channel.id != logging_channel_id:
            await interaction.response.send_message(f"This is only available in <#{logging_channel_id}>", ephemeral=True)
            return
        
        await interaction.response.defer(thinking=True, ephemeral=True)
        description = description.replace("\\n", "\n")
        
        evidences = []
        for evidence in [primary_evidence, evidence2, evidence3, evidence4, evidence5, evidence6, evidence7]:
            if evidence:
                link = await upload(imgbb_key, evidence.url)
                link = link["data"]["display_url"]
                evidences.append(link)

        def determineEmbedColor():
          if observation_type == "Positive":
            return discord.Color.green()
          elif observation_type == "Negative":
            return discord.Color.red()
          elif observation_type == "Information" or "Neutral":
            return discord.Color.lighter_grey()

        def determineEmoji():
          if observation_type == "Positive":
              emoji = ":green_circle:"
              return emoji
          elif observation_type == "Negative":
              emoji = ":red_circle:"
              return emoji
          elif observation_type == "Neutral":
              emoji = ":white_circle:"
              return emoji
          elif observation_type == "Information":
              emoji = ":information_source:"
              return emoji
    
        def determineSpanColor():
          if observation_type == "Positive":
              color = "008000"
              return color
          elif observation_type == "Negative":
              color = "c0392b"
              return color
          else:
              color = "808080"
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

        roblox_username = roblox_username.strip()
        roblox_id = getUserId(roblox_username)
        current_month = datetime.now().month
        current_year = datetime.now().year

        response = await robloxToDiscord(rover_token, server_id, roblox_id)
        discord_id = response['discordUsers'][0]['user']['id']

        class ObservationLayout(discord.ui.Container):
            mediagallery = discord.ui.MediaGallery(discord.MediaGalleryItem("https://i.ibb.co/k2C3f4Lw/image.png"))
            separator1 = discord.ui.Separator()
            text1 = discord.ui.TextDisplay(f"# {determineEmoji()} {"An" if observation_type == "Information" else "A"} {"informational" if observation_type == "Information" else observation_type.lower()} observation was made for {roblox_username} (<@{discord_id}>)")
            text2 = discord.ui.TextDisplay("\n".join(f"> {line}" for line in description.split("\n")))
            author_text = discord.ui.TextDisplay(f"- <@{interaction.user.id}>")
            if primary_evidence:
                evidence_media = discord.ui.MediaGallery()
                for evidence in evidences:
                    if evidence:
                        evidence_media.add_item(media=evidence)

            separator2 = discord.ui.Separator()
            dm_section = discord.ui.Section(ui.TextDisplay("Contact user"), accessory=discord.ui.Button(url=f"https://discord.com/users/{discord_id}", label="DMs"))
            roblox_section = discord.ui.Section(ui.TextDisplay("User's ROBLOX profile"), accessory=discord.ui.Button(url=f"https://roblox.com/users/{roblox_id}/profile", label="ROBLOX"))
            text3 = discord.ui.TextDisplay(f"-# Observation counted towards quota: **{count_towards_quota}**")
            preview_warning = discord.ui.TextDisplay("This is a preview. Verify all information before accepting changes.")
            action_row = discord.ui.ActionRow()


            @action_row.button(label="I've confirmed that the provided information is correct.", style=discord.ButtonStyle.success)
            async def my_button(self, interaction, button):
                try:
                    await interaction.response.defer()
                    comment = f"""
                                <h2>
                                    <span style="color: #{determineSpanColor()}">
                                        <strong>{observation_type}</strong>
                                    </span> 
                                    - Logged by {interaction.user} ({interaction.user.id}) 
                                    {f'<a href={self.evidence_media.items[0].media.url}>(provided proof)</a>' if self.evidence_media.items and self.evidence_media.items[0].media.url else ''}
                                </h2>
                                
                                <blockquote>
                                    {description.replace("\n", "<br>")}
                                </blockquote>
                                {f"<h3>This observation contains extra evidence found in observation-logging.</h3>" if evidence2 is not None else ""}
                                """.strip()
                    user_rank = getRankInGroup(roblox_id)
                    postComment(getId(roblox_username, correctRankId(user_rank)), comment, fc_api_key, correctRankId(user_rank))
        
                    self.remove_item(self.preview_warning)
                    self.remove_item(self.action_row)
                    __import__('pprint').pprint(count_towards_quota)
                    if (observation_type != "Information") and count_towards_quota:
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

                        c.execute(f"INSERT INTO {tableName} (short_date, timestamp) VALUES (?, ?)", ("123", unix_timestamp))
                        conn.commit()
                        c.close()
                        conn.close()
                    else:
                        pass
                    logging_channel_parsed = interaction.client.get_channel(logging_channel_id)
                    await logging_channel_parsed.send(view=self.view)
                    await interaction.followup.send("Observation submitted, logging...", ephemeral=True)
                except Exception as e:
                    print(e)
                    await interaction.channel.send(f"```{e}```")

        my_view = discord.ui.LayoutView()
        cont = ObservationLayout(accent_colour=determineEmbedColor())
        my_view.add_item(cont)

        await interaction.followup.send(view=my_view, ephemeral=True)

    @app_commands.command(
        name='observe-lite',
        description='Submit an observation of a staff member (SMchive ver.)'
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @app_commands.describe(roblox_username="User to log an observation for.", description="Use `\\n` to make a new line, for example \"Hello\\nHello on a new line!\"", primary_evidence="To add more images, you must have primary_evidence uploaded. This will also be seen in FC.")
    @discord.app_commands.checks.has_any_role(1030362797239967845)
    async def observeNew(self, interaction: discord.Interaction, roblox_username: str, observation_type: Literal["Positive", "Negative", "Neutral"], description: str, primary_evidence: discord.Attachment , evidence2: discord.Attachment = None, evidence3: discord.Attachment = None, evidence4: discord.Attachment = None, evidence5: discord.Attachment = None, evidence6: discord.Attachment = None, evidence7: discord.Attachment = None,):
        await interaction.response.defer(thinking=True, ephemeral=True)
        description = description.replace("\\n", "\n")
        
        evidences = []
        for evidence in [primary_evidence, evidence2, evidence3, evidence4, evidence5, evidence6, evidence7]:
            if evidence:
                link = await upload(imgbb_key, evidence.url)
                link = link["data"]["display_url"]
                evidences.append(link)

        def determineEmbedColor():
          if observation_type == "Positive":
            return discord.Color.green()
          elif observation_type == "Negative":
            return discord.Color.red()
          elif observation_type == "Information" or "Neutral":
            return discord.Color.lighter_grey()

        def determineEmoji():
          if observation_type == "Positive":
              emoji = ":green_circle:"
              return emoji
          elif observation_type == "Negative":
              emoji = ":red_circle:"
              return emoji
          elif observation_type == "Neutral":
              emoji = ":white_circle:"
              return emoji
          elif observation_type == "Information":
              emoji = ":information_source:"
              return emoji
    
        def determineSpanColor():
          if observation_type == "Positive":
              color = "008000"
              return color
          elif observation_type == "Negative":
              color = "c0392b"
              return color
          else:
              color = "808080"
              return color

        def correctRankId(chosenRank):
            match chosenRank:
                case "Gamemaster":
                    return gm_id
                case "Trial Moderator":
                    return tm_id
                case "Moderator":
                    return mod_id

        roblox_username = roblox_username.strip()
        roblox_id = getUserId(roblox_username)
        current_month = datetime.now().month
        current_year = datetime.now().year

        response = await robloxToDiscord(rover_token, server_id, roblox_id)
        discord_id = response['discordUsers'][0]['user']['id']

        class ObservationLayout(discord.ui.Container):
            mediagallery = discord.ui.MediaGallery(discord.MediaGalleryItem("https://i.ibb.co/k2C3f4Lw/image.png"))
            separator1 = discord.ui.Separator()
            text1 = discord.ui.TextDisplay(f"# {determineEmoji()} {"An" if observation_type == "Information" else "A"} {"informational" if observation_type == "Information" else observation_type.lower()} observation was made for {roblox_username} (<@{discord_id}>)")
            text2 = discord.ui.TextDisplay("\n".join(f"> {line}" for line in description.split("\n")))
            author_text = discord.ui.TextDisplay(f"- <@{interaction.user.id}>")
            if primary_evidence:
                evidence_media = discord.ui.MediaGallery()
                for evidence in evidences:
                    if evidence:
                        evidence_media.add_item(media=evidence)

            separator2 = discord.ui.Separator()
            dm_section = discord.ui.Section(ui.TextDisplay("Contact user"), accessory=discord.ui.Button(url=f"https://discord.com/users/{discord_id}", label="DMs"))
            roblox_section = discord.ui.Section(ui.TextDisplay("User's ROBLOX profile"), accessory=discord.ui.Button(url=f"https://roblox.com/users/{roblox_id}/profile", label="ROBLOX"))
            preview_warning = discord.ui.TextDisplay("This is a preview. Verify all information before accepting changes.")
            action_row = discord.ui.ActionRow()


            @action_row.button(label="I've confirmed that the provided information is correct.", style=discord.ButtonStyle.success)
            async def my_button(self, interaction, button):
                try:
                    await interaction.response.defer()
                    comment = f"""
                                <h2>
                                    SMchive
                                    <span style="color: #{determineSpanColor()}">
                                        <strong>{observation_type}</strong>
                                    </span> 
                                    - Logged by {interaction.user} ({interaction.user.id}) 
                                    {f'<a href={self.evidence_media.items[0].media.url}>(provided proof)</a>' if self.evidence_media.items and self.evidence_media.items[0].media.url else ''}
                                </h2>
                                
                                <blockquote>
                                    {description.replace("\n", "<br>")}
                                </blockquote>
                                {f"<h3>This observation contains extra evidence found in observation-logging.</h3>" if evidence2 is not None else ""}
                                """.strip()
                    user_rank = getRankInGroup(roblox_id)
                    if user_rank != ("Trial Moderator" or "Gamemaster" or "Moderator"):
                        await interaction.followup.send("Cannot observe this user.")
                    postComment(getId(roblox_username, correctRankId(user_rank)), comment, fc_api_key, correctRankId(user_rank))
        
                    self.remove_item(self.preview_warning)
                    self.remove_item(self.action_row)
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

                    c.execute(f"INSERT INTO {tableName} (short_date, timestamp) VALUES (?, ?)", ("123", unix_timestamp))
                    conn.commit()
                    c.close()
                    conn.close()
                    logging_channel_parsed = interaction.client.get_channel(1429128366887403702)

                    await logging_channel_parsed.send(view=self.view)
                    await interaction.followup.send(f"Observation accepted by {interaction.user}", ephemeral=True)
                except Exception as e:
                    print(e)
                    await interaction.channel.send(f"```{e}```")

        my_view = discord.ui.LayoutView()
        cont = ObservationLayout(accent_colour=determineEmbedColor())
        my_view.add_item(cont)

        await interaction.followup.send("Submitted for review")
        review = interaction.client.get_channel(1429128305289855136)
        await review.send(view=my_view)

    @app_commands.command(
        name='observation-stats',
        description='View the amount of observations made by a specific staff member'
    )
    @app_commands.guilds(discord.Object(id=server_id))
    #@discord.app_commands.checks.has_any_role(observation_access)
    @app_commands.describe(ephemeral="Whether the output should be only seen by you or everyone in the channel")
    async def stats(self, interaction: discord.Interaction, user: discord.Member, ephemeral: bool):
        current_month = datetime.now().month
        current_year = datetime.now().year
        try:
            shortDateNow = datetime.today().replace(day=1)
            shortDateLastMonth = datetime(shortDateNow.year, shortDateNow.month - 1, 1)
            lastDayLastMonth = shortDateLastMonth.replace(day=calendar.monthrange(shortDateLastMonth.year, shortDateLastMonth.month)[1])
            tableName = "o" + str(user.id)
            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            
            queries = [
                f"SELECT COUNT (*) FROM {tableName} WHERE timestamp >= {int(shortDateNow.timestamp())}", 
                f"SELECT COUNT (*) FROM {tableName} WHERE timestamp < {int(shortDateLastMonth.timestamp())} AND timestamp < {int(lastDayLastMonth.timestamp())}", 
                f"SELECT COUNT (*) FROM {tableName}"
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

            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
        except sqlite3.OperationalError as e:
            await interaction.response.send_message(f"SQLite OperationalError: Has the user ever made an observation? Making an observation creates a table. Full traceback:\n```{e}```")

        except Exception as e:
            await interaction.channel.send(e)

    @app_commands.command(
        name='drop-obs-table',
        description='Wipe the observation log for an admin'
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @app_commands.describe(user="!!THIS ACTION IS IRREVERSIBLE!! The admin to get their observation stats wiped.")
    @discord.app_commands.checks.has_any_role(stats_access)
    async def drop_table(self, interaction: discord.Interaction, user: discord.Member):
        if interaction.channel.id != logging_channel_id:
            await interaction.response.send_message(f"This command is only runnable in <#{logging_channel_id}>")
            return
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
            logs_parsed = interaction.client.get_channel(deletion_log)
            await interaction.response.send_message(embed=embed)
            await logs_parsed.send(embed=embed)
            conn.commit()
            c.close()
            conn.close()
        except Exception as e:
            await interaction.channel.send(e)
            
    @app_commands.command(
        name='delete-obs',
        description='Delete a number of observations for a user'
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @app_commands.describe(user="!!THIS ACTION IS IRREVERSIBLE!! The admin to get their observation stats wiped.")
    @discord.app_commands.checks.has_any_role(stats_access)
    async def delete_obs(self, interaction: discord.Interaction, user: discord.Member, number: int):
        try:
            logs_parsed = interaction.client.get_channel(deletion_log)
            embed = discord.Embed(title=f"All data has been irreversibly deleted.",
                description=f"### :warning: {number} Observation stats for <@{user.id}> deleted! \n### This incident will be reported.",
                colour=0xe01b24)

            embed.set_author(name=f"Stats removed by {interaction.user}",
            icon_url=interaction.user.avatar)

            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            c.execute(f"DELETE FROM {"o" + str(user.id)} LIMIT {number}")
            pprint.pprint(f"{interaction.user} has deleted {number} stats for {user.id}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await logs_parsed.send(embed=embed)
            conn.commit()
            c.close()
            conn.close()
        except Exception as e:
            await interaction.channel.send(e)

    @app_commands.command(
        name='leaderboard',
        description='Observation leaderboard for admins'
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role(stats_access)
    async def leaderboard(self, interaction: discord.Interaction):
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        res = c.execute(f"SELECT name FROM sqlite_master WHERE type='table';")
        results = []
        for name in res.fetchall():
            query = c.execute(f"SELECT COUNT (*) FROM {name[0]}")
            count = query.fetchone()[0]
            results.append((name[0][1:], count)) # appends the query results as a tuple to the list, later ill use ts with the paginator library

        L = 10
        sorted_result = sorted(results, key=lambda result: result[1], reverse=True) # results but the tuples are now sorted by the observation count
        async def get_page(page: int):
            emb = discord.Embed(title="LEADERBOARD", description="")
            offset = (page-1) * L
            for result in sorted_result[offset:offset+L]:
                emb.description += f"<@{result[0]}> -- {result[1]}\n"
            emb.set_author(name=f"Requested by {interaction.user}")
            n = Pagination.compute_total_pages(len(results), L)
            emb.set_footer(text=f"Page {page} from {n}")
            return emb, n
        await Pagination(interaction, get_page).navegate()

    @app_commands.command(
        name='image-to-link',
        description='Upload an image to ImgBB with a 6 month expiration date'
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def imgupload(self, interaction: discord.Interaction, image: discord.Attachment):
        await interaction.response.defer(thinking=True, ephemeral=True)
        uploaded = await upload(imgbb_key, image.url)
        print(f"{interaction.user.id} has uploaded image with the link {uploaded["data"]["display_url"]}")
        await interaction.followup.send(f"`{uploaded["data"]["display_url"]}`\n-# Misuse will lead to harsh punishments. This action has been logged.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Observation(bot), guild=discord.Object(id=server_id))
