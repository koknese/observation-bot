from discord import app_commands, ui
from discord.utils import get
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
from typing import Literal  
import os
import time 
import pprint
import discord
import random
import string

signature_req = 15

intents = discord.Intents.all()
intents.members = True

load_dotenv()
server_id = os.getenv('SERVER_ID')
bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree

# For creating progress bars
def generateProgressBar(count:int):
    unsigned_slots = signature_req - count # free slots before the petition is sent, in this case
    bar = []
    for number in range(count): # Adding filled slots to the bar
        if number == 0:
            bar.append("<:ProgLeftFill:1434210384033616133>")
        elif number + 1 == count:
            bar.append("<:ProgEndFill:1434213108762673252>")
        else:
            bar.append("<:ProgMidFill:1434210512601612349>")

    for number in range(unsigned_slots): # adding blank slots to the bar
        if unsigned_slots == 0:
            break
        elif number + 1 == unsigned_slots:
            bar.append("<:ProgEndNull:1434210587692236902>")
        else:
            bar.append("<:ProgMidNull:1434210467022242032>")
    return "".join(bar)

class SignButton(discord.ui.Button):
    def __init__(self, view: 'PetitionMessage') -> None:
        super().__init__(label='Sign Petition', style=discord.ButtonStyle.green, custom_id="signbtn:sign_message")
        self.__view = view

    async def callback(self, interaction: discord.Interaction) -> None:
        # if user not in signees array, get count element and add 1 and edit message with new view
        if interaction.user.id in self.__view.signees:
            self.__view.signees.remove(interaction.user.id)
            self.__view.section_text.content = f"{generateProgressBar(len(self.__view.signees))} | **{len(self.__view.signees)}/{signature_req}**" 
            await interaction.response.edit_message(view=self.__view)
        else:
            self.__view.signees.append(interaction.user.id)
            if len(self.__view.signees) == signature_req:
                self.disabled = True
                self.__view.infoText.content = f"## <:admin:1434205708038967457> This petition will now be considered by the Adminitration."
                self.__view.section_text.content = f"{generateProgressBar(len(self.__view.signees))} | **{len(self.__view.signees)}/{signature_req}**" 
                await interaction.response.edit_message(view=self.__view)
                self.__view.infoText.content = f"## <:admin:1434205708038967457> <@&1030362811215384606>s,a petition was qualified for your consideration."
                channel = interaction.client.get_channel(1434248583946965213)
                await channel.send(view=self.__view)
            else:
                self.__view.section_text.content = f"{generateProgressBar(len(self.__view.signees))} | **{len(self.__view.signees)}/{signature_req}**" 
                await interaction.response.edit_message(view=self.__view)

class PetitionMessage(ui.LayoutView):
    def __init__(self, *, title:str, description: str, user:int) -> None:
        super().__init__(timeout=None)
        self.signees = [user] # setting the interaction user as the only signee at the given moment
        self.titleText = ui.TextDisplay(f"# {title}")
        self.descriptionText = ui.TextDisplay(description)
        self.separator = ui.Separator(visible=True)
        self.section_text = ui.TextDisplay(f"{generateProgressBar(len(self.signees))} | **{len(self.signees)}/{signature_req}**")
        self.signatures = ui.Section(self.section_text, accessory=SignButton(self))
        self.infoText = ui.TextDisplay(f"## <:admin:1434205708038967457> At {signature_req} signatures...\nAt {signature_req} signatures, this petition will be considered for debate in the administration\n-# Proposed by <@{user}>")

        container = ui.Container(
                self.titleText,
                self.descriptionText,
                self.separator,
                self.signatures,
                self.separator,
                self.infoText,
                accent_color=discord.Color.green()
        )
        self.add_item(container)

class Petitions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name="petition",
        description="Make a staff petition"
    )
    @app_commands.checks.cooldown(1,86400)
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role("Game Staff")
    async def petition(self, interaction: discord.Interaction, title: str, description: str):
        channel = interaction.client.get_channel(1434249236345782303)
        message = await channel.send(view=PetitionMessage(title=title, description=description, user=interaction.user.id))
        await message.create_thread(name=title)
        await interaction.response.send_message("Your petition has been made.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Petitions(bot), guild=discord.Object(id=server_id))
