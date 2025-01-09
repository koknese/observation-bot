import discord
from discord import app_commands
from discord.utils import get
from discord.ext import commands
from dotenv import load_dotenv
from typing import Literal
import os

intents = discord.Intents.all()
intents.members = True
server_id = 1184200388665147484
bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    await tree.sync(guild=discord.Object(id=server_id))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"at Risk staff members working"))
    print(discord.__version__)

# insert list of roles that are allowed to run this
role_seniormod = 1241084094184558646 #plwce holder

@tree.command(
    name='observe',
    description='Submit an observation of a staff member',
    guild=discord.Object(id=server_id)
)
@app_commands.describe(user="User to log an observation for.")
@discord.app_commands.checks.has_any_role(role_seniormod)


async def observe(interaction: discord.Interaction, user: discord.Member, observation_type: Literal["Positive", "Negative"], description: str, evidence: discord.Attachment):
  
    def determineEmbedColor():
      if observation_type == "Positive":
        return discord.Color.green()
      elif observation_type == "Negative":
        return discord.Color.red()
    
    embedcolor = determineEmbedColor()
    
    class Buttons(discord.ui.View):
        def __init__(self, *, timeout=180):
            super().__init__(timeout=timeout)

        @discord.ui.button(label="I've verified that the info is correct", style=discord.ButtonStyle.green)
        async def accept_application(self, interaction: discord.Interaction, view: discord.ui.View):
            embed.set_footer(text="Abuse will lead to harsh punishment!")
            await interaction.response.send_message(embed=embed)
            embed.set_author(name=f"You have received a {observation_type.lower()} observation!", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse2.mm.bing.net%2Fth%3Fid%3DOIP.sUVyywAHU0Q2V2hyo_dligAAAA%26pid%3DApi&f=1&ipt=d3f8072407cd9ca31c41b0ab08fa9104c7b3292fdb636a5d6d6e37c0591af2c8&ipo=images")
            embed.set_footer(text="For any questions or concerns, go to the staff-meeting channel in Staff Hub.")
            await user.send(embed=embed)
            
            
          
            # todo: on click, send message in obs channel and in users dms
            pass

    embed = discord.Embed(title=f'Observing {user}', color=embedcolor)
    embed.set_author(name=f"Logged by {interaction.user}", icon_url=str(interaction.user.avatar))
    embed.set_thumbnail(url=evidence.url)
    embed.add_field(name="Description", value=description, inline=True)
    embed.set_footer(text="This is a preview. Click the button below to send submit the observation. Resend the command with correct information if you've made a mistake.")
    await interaction.response.send_message(embed=embed, view=Buttons(), ephemeral=True)

load_dotenv()
token = os.getenv('TOKEN')
bot.run(token)
