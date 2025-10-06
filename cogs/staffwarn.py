from discord import app_commands, ui
from misc.paginator import Pagination
from roblox import Client
from discord.utils import get
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
from typing import Literal  
from misc.rover import discordToRoblox
import os
import time 
import pprint
import discord
import json
import sqlite3

intents = discord.Intents.all()
intents.members = True

load_dotenv()
server_id = os.getenv('SERVER_ID')
roblosecurity = os.getenv("ROBLOSECURITY")
rover_token = os.getenv('ROVER_KEY')

client = Client(roblosecurity)
bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree

def checkUserWarns(userId, warnCat):
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    unix_timestamp = int(time.time()) # horrible but works
    c.execute(f"SELECT COUNT (*) FROM warns WHERE warned_user={userId} AND timestamp >= {unix_timestamp - 15778476} AND warn_category='{warnCat}' AND appealed IS NULL ")
    count = c.fetchone()[0]
    return count

class Staffwarns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name="staff-warn",
        description="Staff warns a user"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role("Administrator")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, description: str, warn_type: Literal["Game staff", "Chat staff"]):
        unix_timestamp = int(time.time()) # horrible but works
        robloxUsername = await discordToRoblox(rover_token, server_id, user.id)
        class ObservationLayout(discord.ui.Container):
            separator1 = discord.ui.Separator()
            text1 = discord.ui.TextDisplay(f"# {f"<@{user.id}>" if warn_type == 'Chat staff' else f"<@{user.id}>" + f' ({robloxUsername["cachedUsername"]})'} has been warned")
            separator2 = discord.ui.Separator()
            text2 = discord.ui.TextDisplay(f"{description}\n**{checkUserWarns(user.id, warn_type) + 1}/2**") # what a horrible workaround i hate this
            separator3 = discord.ui.Separator()
            text3 = discord.ui.TextDisplay(f"-# This is a {warn_type.lower()} only warn ")
        
        my_view = discord.ui.LayoutView()
        cont = ObservationLayout(accent_colour=discord.Color.red())
        my_view.add_item(cont)

        warnChannel = interaction.client.get_channel(1030362795822297109)
        await interaction.response.defer(ephemeral=True)
        conn = sqlite3.connect("data.db")
        c = conn.cursor()
        c.execute(f"""
                CREATE TABLE IF NOT EXISTS warns(
                warned_by INT NOT NULL,
                warned_user INT NOT NULL,
                warn_category TEXT NOT NULL,
				message_id INT NOT NULL,
                appealed INT,
                timestamp INT NOT NULL
                ) 
              """)
        message = await warnChannel.send(view=my_view)
        c.execute(f"INSERT INTO warns(warned_by, warned_user, warn_category, message_id, timestamp) VALUES (?, ?, ?, ?, ?)", (interaction.user.id, user.id, warn_type, message.id, unix_timestamp))
        conn.commit()
        c.close()
        conn.close()
        if checkUserWarns(user.id, warn_type) == 2:
            if warn_type == "Game staff":
                group = await client.get_group(2568175)
                await group.set_rank(robloxUsername["robloxId"], 1)
            # TODO: finish ts up, add chat staff probably


        await interaction.followup.send("Sent!")

    @app_commands.command(
        name="view-warns",
        description="lists a users warns"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role("Administrator")
    async def viewarns(self, interaction: discord.Interaction, user: discord.Member, warn_type:Literal["Game staff", "Chat staff"]):
        conn = sqlite3.connect("data.db")
        unix_timestamp = int(time.time()) # horrible but works
        c = conn.cursor()
        c.execute(f"SELECT * FROM warns WHERE warned_user={user.id} AND warn_category='{warn_type}'AND  timestamp >= {unix_timestamp - 7889238}")
        results = c.fetchall()
        if not results:
            await interaction.response.send_message(f"No warns for <@{user.id}>!", ephemeral=True)
            return

        L = 10
        # sorted_result = sorted(results, key=lambda result: result[1], reverse=True) # results but the tuples are now sorted by the observation count
        async def get_page(page: int):
            emb = discord.Embed(title=f"Staff warns for {user} ({checkUserWarns(user.id, warn_type)}/2)", description="")
            offset = (page-1) * L
            for result in results[offset:offset+L]:
                if result[5] != 1:
                    emb.description += f"<@{result[0]}> -- https://discord.com/channels/252552812427214849/1030362795822297109/{result[3]}\n"
                else:
                    emb.description += f"~~<@{result[0]}> -- https://discord.com/channels/252552812427214849/1030362795822297109/{result[3]}~~\n"
                
            emb.set_author(name=f"Requested by {interaction.user}. Expired warns are not shown.")
            n = Pagination.compute_total_pages(len(results), L)
            emb.set_footer(text=f"Page {page} from {n}")
            return emb, n
        await Pagination(interaction, get_page).navegate()
        conn.commit()
        c.close()
        conn.close()



    @app_commands.command(
        name="appeal",
        description="appeal a warn"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @discord.app_commands.checks.has_any_role("Administrator")
    async def deletewarn(self, interaction: discord.Interaction, user: discord.Member, message_id: str, reason: str, warn_type:Literal["Game staff", "Chat staff"]):
        class ObservationLayout(discord.ui.Container):
            text1 = discord.ui.TextDisplay(f"# Staff warn for f<@{user.id}> appealed!")
            separator1 = discord.ui.Separator()
            text2 = discord.ui.TextDisplay(f"{reason}\n**{checkUserWarns(user.id, warn_type) - 1}/2**") # what a horrible workaround i hate this
            separator3 = discord.ui.Separator()
        
        conn = sqlite3.connect("data.db")
        c = conn.cursor()
        c.execute(f"UPDATE warns SET appealed=1 WHERE message_id={message_id}")
        conn.commit()
        c.close()
        conn.close()

        my_view = discord.ui.LayoutView()
        cont = ObservationLayout(accent_colour=discord.Color.green())
        my_view.add_item(cont)

        warnChannel = interaction.client.get_channel(1030362795822297109)
        message_id = int(message_id)
        message = await warnChannel.fetch_message(message_id)
        await message.reply(view=my_view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Staffwarns(bot), guild=discord.Object(id=server_id))
