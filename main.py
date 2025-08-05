import discord
import hmac
import hashlib
import requests
from discord import app_commands, Embed
from discord.utils import get
from discord.ext import commands
from dotenv import load_dotenv
from typing import Literal  
import os
import time 
import pprint
from misc.paginator import Pagination

intents = discord.Intents.all()
intents.members = True

load_dotenv()
server_id = os.getenv('SERVER_ID')
fc_secret = os.getenv('API_SECRET')
fc_api_key = os.getenv('API_KEY')
fc_app_id = os.getenv('APP_ID')
observation_access = int(os.getenv('OBS_ROLE'))

timestamp = int(time.time() * 1000)  
hash_bytes = hmac.new(fc_secret.encode(), (fc_api_key + str(timestamp)).encode(), hashlib.sha1).digest()
hash_string = hash_bytes.hex()

bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree

def getId(username):
    params = {
        "api_key": fc_api_key,
        "hash": hash_string,
        "timestamp": timestamp
    }
    url = "https://freedcamp.com/api/v1/tasks"
    response = requests.get(url, params=params)
    if response.status_code == 200:
        r = response.json()
    
        def getTaskByTitle():
            for task in r["data"]["tasks"]:
                if task["title"] == username:
                    return task
            return None

        pprint.pprint(getTaskByTitle()["id"])
        if getTaskByTitle():
            return getTaskByTitle()["id"]
        else:
            return None
    else:
        print(f"Error: {response.text}")

def postComment(task_id, contents, api_key, hash_string):
    url = f"https://freedcamp.com/api/v1/comments"
    params = {
        "api_key": api_key,
        "hash": hash_string,
        "timestamp": timestamp
    }
    data = {
        "description": contents,
        "app_id": fc_app_id,
        "task_id": task_id
    }

    response = requests.post(url, json=data, params=params)

    if response.status_code == 200:
        pprint.pprint(response.json())
    else:
        pprint.pprint(f"Error: {response.status_code}")
        pprint.pprint(response.text)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    await tree.sync(guild=discord.Object(id=server_id))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"Risk staff members working"))
    print(discord.__version__)

@tree.command(
    name='observe',
    description='Submit an observation of a staff member',
    guild=discord.Object(id=server_id)
)
@app_commands.describe(roblox_username="User to log an observation for.")
@discord.app_commands.checks.has_any_role(observation_access)
async def observe(interaction: discord.Interaction, roblox_username: str, observation_type: Literal["Positive", "Negative"], description: str, evidence: discord.Attachment):
  
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
    
    embedcolor = determineEmbedColor()
    
    class Buttons(discord.ui.View):
        def __init__(self, *, timeout=180):
            super().__init__(timeout=timeout)

        @discord.ui.button(label="I've verified that the info is correct", style=discord.ButtonStyle.green)
        async def accept_application(self, interaction: discord.Interaction, view: discord.ui.View):
            try:
                #updatedDesc = f"{getDesc(roblox_username)}\n\n<p><span style=\"color:#{determineSpanColor()}><strong>{observation_type}</strong></span> - Logged by {interaction.user.id} <a href=\"{evidence.url}\">(provided proof)</a></p>\n\n<blockquote>\n\n{description}\n\n</blockquote>\n\n<p>=======================</p>"
                comment = f"""
                            <h2>
                                <span style="color: #{determineSpanColor()}">
                                    <strong>{observation_type}</strong>
                                </span> 
                                - Logged by {interaction.user}({interaction.user.id}) 
                                <a href="{evidence.url}">(provided proof)</a>
                            </h2>
                            
                            <blockquote>
                                {description}
                            </blockquote>
                            """.strip()


                postComment(getId(roblox_username), comment, fc_api_key, hash_string)

                embed.set_footer(text="Abuse will lead to harsh punishment!")
                await interaction.response.send_message(embed=embed)
            except Exception as e:
                await interaction.response.send_message(f"An error has occured:\n```{e}```")

    embed = discord.Embed(title=f'Observing {roblox_username}', color=embedcolor)
    embed.set_author(name=f"Logged by {interaction.user}", icon_url=str(interaction.user.avatar))
    embed.set_thumbnail(url=evidence.url)
    embed.add_field(name="Description", value=description, inline=True)
    embed.set_footer(text="This is a preview. Click the button below to send submit the observation. Resend the command with correct information if you've made a mistake.")
    await interaction.response.send_message(embed=embed, view=Buttons(), ephemeral=True)

token = os.getenv('TOKEN')
bot.run(token)
