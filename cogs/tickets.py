from misc.rover import robloxToDiscord, discordToRoblox
from misc.paginator import Pagination
from cogs.rolemanipulation import ranklist
from discord import app_commands, ui
from discord.utils import get
from ast import literal_eval
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
from typing import Literal  
import os
import io
import random
import time 
import pprint
import discord
import json
import requests
import aiohttp
import asyncio
import chat_exporter
import string

intents = discord.Intents.all()
intents.members = True
ID_API_ENDPOINT = "https://users.roblox.com/v1/usernames/users"

load_dotenv()
server_id = os.getenv('SERVER_ID')
fc_secret = os.getenv('API_SECRET')
rover_token = os.getenv('ROVER_KEY')
fc_api_key = os.getenv('API_KEY')
inactivity_channel = int(os.getenv("INACTIVITY_CHANNEL"))

mod_id = os.getenv('MOD_ID')
sm_id = os.getenv('SM_ID')
gm_id = os.getenv('GM_ID')
tm_id = os.getenv('TM_ID')

observation_access = int(os.getenv('OBS_ROLE'))

bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree


def getUserId(username):
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

async def getRankInGroupAsync(userid, groupId):
    if userid:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://groups.roblox.com/v1/users/{userid}/groups/roles") as request:
                response = await request.json()
                for i in response["data"]:
                    if i["group"]["id"] == groupId:
                        return i["role"]["rank"]
    else:
        error = "User ID couldn't be found or user not in group."
        return error

async def getHighestRank(userid):
    if userid:
        oldRank = await getRankInGroupAsync(userid, 2568175)
        newRank = await getRankInGroupAsync(userid, 640802959)
        if newRank >= oldRank:
            return newRank
        else:
            return oldRank
    else:
        error = "User ID couldn't be found or user not in group."
        return error


class QuestionModal(discord.ui.Modal, title='Question'):
        def __init__(self):
            super().__init__()

        description = ui.TextInput(label='Your question', placeholder="joe many liberals dose it take to cahnge log by bold", style=discord.TextStyle.long)
        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                talk = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    attach_files=True
                )
                adminRole = await interaction.guild.fetch_role(observation_access)
                inactiveAdmins = await interaction.guild.fetch_role(1194693804192706620)
                async def getRandomAdmin():
                    foundSuitableAdmin = False
                    while foundSuitableAdmin == False:
                        randomAdmin = random.choice(adminRole.members)
                        if randomAdmin in inactiveAdmins.members:
                            continue
                        else:
                            foundSuitableAdmin = True
                            return randomAdmin
                            break

                category = discord.utils.get(interaction.guild.categories, id=1030362769108770876)
                randomAdmin = await getRandomAdmin()
                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    interaction.guild.me: talk,
                    adminRole:talk,
                    interaction.user:talk
                }
                def randomword(length):
                    letters = string.ascii_lowercase
                    return ''.join(random.choice(letters) for i in range(length))
                embed = discord.Embed()
                createdChannel = await interaction.guild.create_text_channel(f"question-{interaction.user.name}-{randomword(3)}", overwrites=overwrites, category=category, topic=f"{{ 'report': False }}")
                embed.add_field(name="Question",
                                value=self.description.value,
                                inline=False)
                await createdChannel.send(f"<@{interaction.user.id}>, administrator <@{randomAdmin.id}> is assigned to your ticket.", embed=embed)
                await interaction.followup.send(f'Your ticket has been created: <#{createdChannel.id}>', ephemeral=True)
            except Exception as e:
                raise e
                await interaction.followup.send(e, ephemeral=True)
                return

class ReportModal(discord.ui.Modal, title='Reporting a staff member'):
        def __init__(self):
            super().__init__()
        images = discord.ui.Label(
                text='Evidence',
                description='Upload any evidence. IMAGES ONLY.',
                component=discord.ui.FileUpload(
                    max_values=10,
                    custom_id='evidence_imgs',
                    required=True,
                ),
        )
        user = ui.TextInput(label='User to report', placeholder="saltbear1 (ROBLOX username)", style=discord.TextStyle.short)
        description = ui.TextInput(label='Report description', placeholder="help heplhpe help fp fp fp fp", style=discord.TextStyle.long)
        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                talk = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    attach_files=True
                )
                adminRole = await interaction.guild.fetch_role(observation_access)
                inactiveAdmins = await interaction.guild.fetch_role(1194693804192706620)
                async def getRandomAdmin():
                    foundSuitableAdmin = False
                    while foundSuitableAdmin == False:
                        randomAdmin = random.choice(adminRole.members)
                        if randomAdmin in inactiveAdmins.members:
                            continue
                        else:
                            foundSuitableAdmin = True
                            return randomAdmin
                            break

                category = discord.utils.get(interaction.guild.categories, id=1030362769108770876)
                randomAdmin = await getRandomAdmin()
                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    interaction.guild.me: talk,
                    adminRole:talk,
                    interaction.user:talk
                }
                def randomword(length):
                    letters = string.ascii_lowercase
                    return ''.join(random.choice(letters) for i in range(length))
                embed = discord.Embed()

                evidences = []
                async def getRoleName(rank):
                    for key, value in ranklist.items():
                        if value == rank:
                            return key
                
                target = self.user.value.strip()
                rank = await getHighestRank(getUserId(target))
                __import__('pprint').pprint(rank)
                if rank <= 2 or not isinstance(rank, int) or not rank:
                    await interaction.followup.send("User does not exist or is not above the EXP+ threshold!")
                    return

                role = await getRoleName(rank)
                createdChannel = await interaction.guild.create_text_channel(f"report-{self.user.value.strip()}-{randomword(3)}", overwrites=overwrites, category=category, topic=f"{{ 'report': True, 'target':\"{self.user.value.strip()}\", 'targetRank':'{role}' }}")

                                
                for evidence in self.images.component.values:
                    if evidence:
                        evidences.append(evidence.url)

                embed.add_field(name="Reporter",
                                value=f"<@{interaction.user.id}>",
                                inline=True)
                embed.add_field(name="Target",
                                value=f"{role} {target}",
                                inline=False)
                embed.add_field(name="description",
                                value=self.description.value,
                                inline=False)
                await createdChannel.send(f"<@{interaction.user.id}>, administrator <@{randomAdmin.id}> is assigned to your ticket.", embed=embed)
                await createdChannel.send(f"Provided evidence:\n {'\n'.join(evidences)}\n\nAdministrator, remember to run `/close-report` upon finishing the ticket!")
                await interaction.followup.send(f'Your ticket has been created: <#{createdChannel.id}>', ephemeral=True)
            except IndexError:
                await interaction.followup.send("IndexError: You likely made a typo in the username as the user does not exist/is not part of any Risk groups.", ephemeral=True)
            except Exception as e:
                raise e
                await interaction.followup.send(e, ephemeral=True)
                return

class Dropdown(discord.ui.Select):
    def __init__(self):
        options = [
                discord.SelectOption(label='Staff reports', description='Report EXP+ misdeeds. Can also be used for positive interactions.', emoji='⚠️', value="report"),
                discord.SelectOption(label='General inquiry', description='For general questions and staff meetings', emoji='❔', value="question")
        ]
        super().__init__(placeholder='Choose ticket type', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "report":
            await interaction.response.send_modal(ReportModal())
        else:
            await interaction.response.send_modal(QuestionModal())

class DropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Dropdown())

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name="create-dropdown",
        description="DEBUG: Create a ticket prompt"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role("Developer")
    async def createDropdown(self, interaction:discord.Interaction):
        await interaction.channel.send("You can open tickets here:", view=DropdownView())

    @app_commands.command(
        name="close-report",
        description="Close a staff report"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role("Administrator", "Head Administrator", "Director")
    async def closeReport(self, interaction:discord.Interaction, action_taken:str):
        category = discord.utils.get(interaction.guild.categories, id=1030362769108770876)
        if interaction.channel.category == category:
            __import__('pprint').pprint(interaction.channel.topic)
            smartTopic = literal_eval(interaction.channel.topic)
            __import__('pprint').pprint(smartTopic)
            logging = interaction.client.get_channel(1549119468939120720)  # hicom backups channel
            loggingPublic = interaction.client.get_channel(1030362848976719902)  # admin transcripts 
            await interaction.response.send_message("Closing...")
            transcript = await chat_exporter.export(
                interaction.channel,
                limit=200,
                tz_info="UTC",
                military_time=True,
                bot=interaction.client,
            )

            if transcript is None:
                return

            transcript_file = discord.File(
                io.BytesIO(transcript.encode()),
                filename=f"transcript-{interaction.channel.name}.html",
            )
            message = None
            if smartTopic["report"]:
                message = await logging.send(f"{interaction.user} has closed a report.\n**Target:**{smartTopic['target']} ({smartTopic["targetRank"]})\n**Reason:** `{action_taken}`", file=transcript_file)
            else:
                message = await logging.send(f"{interaction.user} has closed an admin question.\nReason: `{reason}`", file=transcript_file)
            await message.forward(loggingPublic)
            await interaction.channel.delete(reason="Closed")

        else:
            await interaction.response.send_message("Not a mod-assistance ticket", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot), guild=discord.Object(id=server_id))
