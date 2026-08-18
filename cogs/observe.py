from misc.rover import robloxToDiscord
from misc.imgbb import upload
from misc.paginator import Pagination
from misc.freedcamp import Freedcamp
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
smchive_logging = int(os.getenv("SMCHIVE_LOGGING"))
imgbb_key = os.getenv("IMGBB_KEY")
deletion_log = int(os.getenv("DELETION_LOGS"))

mod_id = os.getenv('MOD_ID')
sm_id = os.getenv('SM_ID')
gm_id = os.getenv('GM_ID')
tm_id = os.getenv('TM_ID')

observation_access = int(os.getenv('OBS_ROLE'))
stats_access = int(os.getenv('HA_ROLE'))

freedcamp = Freedcamp(fc_api_key, fc_secret)

bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree

def getUserId(username, interaction = None):
    try:
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
    except Exception as e:
        return None

def getRankInGroup(userid):
    if userid:
        request = requests.get(f"https://groups.roblox.com/v1/users/{userid}/groups/roles")
        response = json.loads(request.text)
        for i in response["data"]:
            if i["group"]["id"] == 640802959:
                return i["role"]["name"]
    else:
        error = "User ID couldn't be found or user not in group."
        return error

class ObservationLayout(ui.LayoutView):
    def __init__(self, *,interactionUserId:int, span_color:any, emoji:str, rank_id:int, fc_task_id:int, discord_id:int, roblox_id:int, count_towards_quota:bool, evidences:any, observation_type:str, roblox_username:str, description) -> None:
        super().__init__(timeout=None)
        self.separator = ui.Separator(visible=True)
        self.invisSeparator = ui.Separator(visible=False)
        self.author_text = discord.ui.TextDisplay(f"- <@{interactionUserId}>")
        self.banner = discord.ui.MediaGallery(discord.MediaGalleryItem("https://i.ibb.co/k2C3f4Lw/image.png"))
        self.title = discord.ui.TextDisplay(f"# {emoji} {"An" if observation_type == "info" else "A"} {"informational" if observation_type == "info" else observation_type.lower()} observation was made for {roblox_username} (<@{discord_id}>)")
        self.body = discord.ui.TextDisplay("\n".join(f"> {line}" for line in description.split("\n")))
        self.evidence_media = discord.ui.MediaGallery()
        if evidences != []:
            for evidence in evidences:
                if evidence:
                    self.evidence_media.add_item(media=evidence)

        self.dm_section = discord.ui.Section(ui.TextDisplay("Contact user"), accessory=discord.ui.Button(url=f"https://discord.com/users/{discord_id}", label="DMs"))
        self.roblox_section = discord.ui.Section(ui.TextDisplay("User's ROBLOX profile"), accessory=discord.ui.Button(url=f"https://roblox.com/users/{roblox_id}/profile", label="ROBLOX"))
        self.task_section = discord.ui.Section(ui.TextDisplay("User's Freedcamp task"), accessory=discord.ui.Button(url=f"https://freedcamp.com/view/{rank_id}/tasks/panel/task/{fc_task_id}", label="Freedcamp task"))
        self.footer= discord.ui.TextDisplay(f"-# Observation counted towards quota: **{count_towards_quota}**")

        container = ui.Container(
                self.banner,
                self.separator,
                self.title,
                self.body,
                self.author_text,
                self.evidence_media if evidences != [] else self.invisSeparator,
                self.separator,
                self.dm_section,
                self.roblox_section,
                self.task_section,
                self.footer,
                accent_color=span_color
        )
        self.add_item(container)

class Observation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None


    class ObserveModal(discord.ui.Modal, title='Observing a user'):
        def __init__(self, observer):
            self.observer = observer 
            super().__init__()
        images = discord.ui.Label(
                text='Evidence',
                description='Upload any evidence. IMAGES ONLY.',
                component=discord.ui.FileUpload(
                    max_values=10,
                    custom_id='evidence_imgs',
                    required=False,
                ),
        )
        observation_type = discord.ui.Label(
                text='Observation type',
                description='Choose the type of observation',
                component=discord.ui.Select(
                    max_values=1,
                    custom_id='observation_type',
                    required=True,
                    options = [
                        discord.SelectOption(label="Positive", value="positive", emoji="🟢", description="For good deeds by the staff"),
                        discord.SelectOption(label="Negative", value="negative", emoji="🔴", description="For the misdeeds by the staff"),
                        discord.SelectOption(label="Neutral", value="neutral", emoji="🔲", description="Schrodingers observation"),
                        discord.SelectOption(label="Informational", value="info", emoji="ℹ️", description="For notices, addendums, etc.")
                    ]
                ),
        )
        user = ui.TextInput(label='User to observe', placeholder="saltbear1 (ROBLOX usernames)", style=discord.TextStyle.short)
        description = ui.TextInput(label='Observation description', placeholder="saltbear owes me 60k robux. neg obs", style=discord.TextStyle.long)
        count_towards_quota = discord.ui.Label(text="Count towards quota?", component=discord.ui.Checkbox())
        async def on_submit(self, interaction: discord.Interaction):
            try:
                await interaction.response.defer(thinking=True, ephemeral=True)
                loading = await interaction.followup.send(f"<a:loading:1424337544891338784> Uploading evidence...")
                observation_type = self.observation_type.component.values[0]
                evidences = []
                for evidence in self.images.component.values:
                    if evidence:
                        link = await upload(imgbb_key, evidence.url)
                        link = link["data"]["url"]
                        evidences.append(link)
                await loading.edit(content=f"<a:loading:1424337544891338784> Getting user IDs...")
                roblox_username = self.user.value.strip()
                roblox_id = getUserId(roblox_username)
                if roblox_id == None:
                    await interaction.followup.send(f"No Roblox user `${roblox_username}` was found", ephemeral=True)
                    return
                response = await robloxToDiscord(rover_token, server_id, roblox_id)
                discord_id = response['discordUsers'][0]['user']['id']

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

                await loading.edit(content=f"<a:loading:1424337544891338784> Getting user task...")
                user_rank = getRankInGroup(roblox_id)
                fc_task_id = await freedcamp.getId(roblox_username, correctRankId(user_rank))
                if fc_task_id == None:
                    await interaction.followup.send(f"No task for user `${roblox_username}` was found", ephemeral=True)
                    return

                def determineEmbedColor(observation_type):
                    if observation_type == "positive":
                      return discord.Color.green()
                    elif observation_type == "negative":
                      return discord.Color.red()
                    else:
                      return discord.Color.lighter_grey()

                def determineSpanColor(observation_type):
                    if observation_type == "positive":
                        color = "008000"
                        return color
                    elif observation_type == "negative":
                        color = "c0392b"
                        return color
                    else:
                        color = "808080"
                        return color

                def determineEmoji(observation_type):
                  if observation_type == "positive":
                      emoji = ":green_circle:"
                      return emoji
                  elif observation_type == "negative":
                      emoji = ":red_circle:"
                      return emoji
                  elif observation_type == "neutral":
                      emoji = ":white_circle:"
                      return emoji
                  elif observation_type == "info":
                      emoji = ":information_source:"
                      return emoji


                await loading.edit(content=f"<a:loading:1424337544891338784> Uploading the observation to Freedcamp...")
                comment = f"""
                            <h2>
                                <span style="color: #{determineSpanColor(observation_type)}">
                                    <strong>{observation_type.capitalize()}</strong>
                                </span> 
                                - Logged by {interaction.user} ({interaction.user.id}) 
                                {f'<a href={evidences[0]}>(provided proof)</a>' if evidences != [] else ''}
                            </h2>
                            
                            <blockquote>
                                {self.description.value.replace("\n", "<br>")}
                            </blockquote>
                            {f"<h3>This observation contains extra evidence found in observation-logging.</h3>" if len(evidences) >= 2 else ""}
                            """.strip()
                await freedcamp.postComment(fc_task_id, comment, correctRankId(user_rank))
                if (observation_type != "Information") and self.count_towards_quota.component.value:
                    await loading.edit(content=f"<a:loading:1424337544891338784> Registering observation to your stats...")
                    conn = sqlite3.connect("data.db")
                    c = conn.cursor()
                    tableName = "o" + str(interaction.user.id) # bypassing sqlite not allowing numbers as table names
                    c.execute(f"""CREATE TABLE IF NOT EXISTS {tableName}(
                            short_date TEXT NOT NULL,
                            timestamp TEXT NOT NULL
                            ) 
                          """)

                    unix_timestamp = str(int(time.time())) # horrible but works

                    c.execute(f"INSERT INTO {tableName} (short_date, timestamp) VALUES (?, ?)", ("123", unix_timestamp))
                    conn.commit()
                    c.close()
                    conn.close()
                logging_channel_parsed = interaction.client.get_channel(logging_channel_id)
                await loading.edit(content=f"✅ Done!")
                await logging_channel_parsed.send(view=ObservationLayout(
                    interactionUserId=interaction.user.id,
                    span_color=determineEmbedColor(observation_type),
                    emoji=determineEmoji(observation_type),
                    rank_id=correctRankId(user_rank),
                    fc_task_id=fc_task_id,
                    discord_id=discord_id,
                    roblox_id=roblox_id,
                    count_towards_quota=self.count_towards_quota.component.value,
                    evidences=evidences,
                    observation_type=observation_type,
                    roblox_username=self.user.value,
                    description=self.description.value
                ))
                
            except Exception as e:
                print(e)
                await interaction.channel.send(f"```{e}```")

    @app_commands.command(
        name='observe',
        description='Submit an observation of a staff member'
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role(observation_access)
    async def observe(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.ObserveModal(interaction.user.id))
    @app_commands.command(
        name='observation-stats',
        description='View the amount of observations made by a specific staff member'
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role(observation_access)
    @app_commands.describe(ephemeral="Whether the output should be only seen by you or everyone in the channel")
    async def stats(self, interaction: discord.Interaction, user: discord.Member, ephemeral: bool):
        current_month = datetime.now().month
        current_year = datetime.now().year
        try:
            shortDateNow = datetime.today().replace(day=1)
            
            # Handle the case when the current month is January
            if shortDateNow.month == 1:
                shortDateLastMonth = datetime(shortDateNow.year - 1, 12, 1)
            else:
                shortDateLastMonth = datetime(shortDateNow.year, shortDateNow.month - 1, 1)

            lastDayLastMonth = shortDateLastMonth.replace(day=calendar.monthrange(shortDateLastMonth.year, shortDateLastMonth.month)[1])
            tableName = "o" + str(user.id)
            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            
            queries = [
                f"SELECT COUNT (*) FROM {tableName} WHERE timestamp >= {int(shortDateNow.timestamp())}", 
                f"SELECT COUNT (*) FROM {tableName} WHERE timestamp >= {int(shortDateLastMonth.timestamp())} AND timestamp <= {int(lastDayLastMonth.timestamp())}", 
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
        print(f"{interaction.user.id} has uploaded image with the link {uploaded["data"]["url"]}")
        await interaction.followup.send(f"`{uploaded["data"]["url"]}`\n-# Misuse will lead to harsh punishments. This action has been logged.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Observation(bot), guild=discord.Object(id=server_id))
