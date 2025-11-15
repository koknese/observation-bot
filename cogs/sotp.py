from discord import app_commands, ui
from misc.rover import discordToRoblox
from discord.utils import get
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
from typing import Literal, Any
from cogs.modassistance import getHeadshot
import os
import time 
import discord
import random
import string

intents = discord.Intents.all()
intents.members = True

load_dotenv()
server_id = os.getenv('SERVER_ID')
bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree

class CampaignMessage(ui.LayoutView):
    def __init__(self, *, user:int, roblox_user:str, roblox_portrait:str, time_in_risk:str, description:str, image:str = None) -> None:
        super().__init__(timeout=None)
        self.thumbnail = ui.Thumbnail(media=getHeadshot(roblox_id))
        self.banner = ui.MediaGallery(discord.MediaGalleryItem("https://i.ibb.co/k2C3f4Lw/image.png")) # setting the interaction user as the only signee at the given moment
        self.titleText = ui.TextDisplay(f"# <@{user}>'s bid for Senator")
        self.sloganText = ui.TextDisplay(f"### <@{user}>'s bid for Senator")
        self.infoText = ui.Section(ui.TextDisplay(f"**Risk member for**: *{time_in_risk}*\n**Roblox username**: `{roblox_user}`"), accessory=1)
        self.descriptionText = ui.TextDisplay(description)
        self.gallery = ui.MediaGallery(discord.MediaGalleryItem(image)) if image else None # setting the interaction user as the only signee at the given moment
        self.separator = ui.Separator(visible=True)

        container = ui.Container(
                self.banner,
                self.titleText,
                self.separator,
                self.infoText,
                self.separator,
                self.sloganText
                self.descriptionText,
                self.separator,
                self.gallery,
                accent_color=discord.Color.green()
        )
        self.add_item(container)

class Petitions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name="bid",
        description="Make a bid for Senator of Participants"
    )
    @app_commands.checks.cooldown(1,900000)
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role("Participant", "Experienced Participant", "Trusted Participant")
    async def petition(self, interaction: discord.Interaction, slogan:str, description: str, time_in_risk:str, image:discord.Attachment = None):
        channel = interaction.client.get_channel(1402736513543831583)
        response_data = await roverResponse 
        userIdRover = response_data["robloxId"]
        usernameRover = response_data["cachedUsername"]
        message = await channel.send(view=CampaignMessage(description=description, user=interaction.user.id, roblox_user=usernameRover, time_in_risk=time_in_risk, image=image.url, roblox_portrait=getHeadshot(userIdRover)))
        await interaction.response.send_message("Your bid has been made.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Petitions(bot), guild=discord.Object(id=server_id))
