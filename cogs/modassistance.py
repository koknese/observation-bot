import discord
import requests
import sqlite3
from misc.rover import discordToRoblox
from discord import app_commands, Embed, ui
from discord.utils import get
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
from typing import Literal
import os
import time 
import pprint

intents = discord.Intents.all()
intents.members = True

ID_API_ENDPOINT = "https://users.roblox.com/v1/usernames/users"
load_dotenv("../.env")
server_id = os.getenv('SERVER_ID')
assistance_channel = os.getenv('ASSISTANCE_CHANNEL')
rover_token = os.getenv('ROVER_KEY')
game_staff_role = os.getenv("GS_ROLE")
# converts username to user headshot
def getHeadshot(userId):
    userRawHeadshot = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={userId}&format=png&size=352x352"
    response = requests.get(userRawHeadshot)
    if response.status_code == 200:
        userParsedHeadshot = response.json()
        userFinalHeadshot = userParsedHeadshot['data'][0]['imageUrl']
        print(f"getHeadshot :: Fetched headshot of {userId}")
        return userFinalHeadshot
    else:
        placeholderImg = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fi.imgflip.com%2Fd0tb7.jpg&f=1&nofb=1&ipt=e1c23bf6c418254a56c19b09cc9ece6238ead393652e54278f0d535f9fb81c56"
        return placeholderImg

class Closebutton(ui.View):
    def __init__(self, interaction_user, message, thread):
        super().__init__()
        self.interaction_user = interaction_user
        self.message = message
        self.thread = thread
        button = discord.ui.Button(label='Close ticket', style=discord.ButtonStyle.red)
        button.callback = self.close_ticket
        self.add_item(button)

    async def close_ticket(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(int(game_staff_role))
        if (interaction.user.id == self.interaction_user) or (role in interaction.user.roles):
            await interaction.response.send_message(f"<@{interaction.user.id}>, deleting thread and message...")
            await self.thread.delete(reason="Closed")
            await self.message.delete()
        else:
            await interaction.response.send_message("No permissions to delete ticket", ephemeral=True)


class Assistance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name="mod-assistance",
        description="Call for mod assistance for in-game support"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def assistance(self, interaction:discord.Interaction, urgency:Literal["Low","Medium", "High"], description:str, server_era: str, image: discord.Attachment = None):
        userIdRover = discordToRoblox(rover_token, server_id, interaction.user.id)["robloxId"]
        usernameRover = discordToRoblox(rover_token, server_id, interaction.user.id)["cachedUsername"]
        await interaction.response.defer(thinking=True, ephemeral=True)
        embed = discord.Embed(title=f"Assistance needed in {server_era}!",
                      url=f"https://www.roblox.com/users/{userIdRover}/profile",
                      colour=0x00b0f4)

        embed.set_author(name=interaction.user,
                         url=f"https://www.roblox.com/users/{userIdRover}/profile",
                         icon_url=interaction.user.avatar.url if interaction.user.avatar != None else interaction.user.display_avatar.url)
        
        embed.add_field(name="Urgency",
                        value=urgency,
                        inline=False)

        embed.add_field(name="Caller",
                        value=f"{interaction.user} ({usernameRover})",
                        inline=False)
        embed.add_field(name="description",
                value=description,
                inline=False)

        embed.add_field(name="Era",
                value=server_era,
                inline=False)
        embed.set_thumbnail(url=getHeadshot(userIdRover))
        embed.set_image(url=image.url if image else None)

        assistance_channel_parsed = interaction.client.get_channel(int(assistance_channel))

        message = await assistance_channel_parsed.send(embed=embed)
        thread = await message.create_thread(name=f"{urgency} :: {usernameRover}", auto_archive_duration=60)
        await thread.send(f"<@{interaction.user.id}> :: <@&1030362803757924452>", view=Closebutton(interaction.user.id, message, thread))
        await interaction.followup.send("Sent!", ephemeral=True)
        
async def setup(bot: commands.Bot):
    await bot.add_cog(Assistance(bot), guild=discord.Object(id=server_id))
