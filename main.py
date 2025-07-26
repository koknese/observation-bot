import discord
from discord import app_commands, Embed
from discord.utils import get
from discord.ext import commands
from dotenv import load_dotenv
from typing import Literal  
import os
import time 
import sqlite3
from misc.paginator import Pagination

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

@tree.command(
    name='observe',
    description='Submit an observation of a staff member',
    guild=discord.Object(id=server_id)
)
@app_commands.describe(user="User to log an observation for.")
@discord.app_commands.checks.has_any_role(1398653755519537284)
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
            try:
                conn = sqlite3.connect('data.db')
                c = conn.cursor()
                
                # what a cheeky workaround...
                tableName = "o" + str(user.id)
                c.execute(f"""CREATE TABLE IF NOT EXISTS {tableName}( 
                                 observation_type TEXT NOT NULL,
                                 description TEXT NOT NULL,
                                 date TEXT NOT NULL,
                                 screenshot TEXT NOT NULL,
                                 reviewer_id BIGINT NOT NULL
                                 )""")

                unix_timestamp = int(time.time())

                c.execute(f"""INSERT INTO {tableName} (observation_type, description, date, screenshot, reviewer_id) 
                          VALUES (?, ?, ?, ?, ?)""", (observation_type, description, unix_timestamp, evidence.url, interaction.user.id))
                embed.set_footer(text="Abuse will lead to harsh punishment!")
                await interaction.response.send_message(embed=embed)
                embed.set_author(name=f"You have received a {observation_type.lower()} observation!", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse2.mm.bing.net%2Fth%3Fid%3DOIP.sUVyywAHU0Q2V2hyo_dligAAAA%26pid%3DApi&f=1&ipt=d3f8072407cd9ca31c41b0ab08fa9104c7b3292fdb636a5d6d6e37c0591af2c8&ipo=images")
                embed.set_footer(text="For any questions or concerns, go to the staff-meeting channel in Staff Hub.")
                await user.send(embed=embed)

                conn.commit()
                c.close()
                conn.close()
            except Exception as e:
                await interaction.response.send_message(f"An error has occured:\n```{e}```")

    embed = discord.Embed(title=f'Observing {user}', color=embedcolor)
    embed.set_author(name=f"Logged by {interaction.user}", icon_url=str(interaction.user.avatar))
    embed.set_thumbnail(url=evidence.url)
    embed.add_field(name="Description", value=description, inline=True)
    embed.set_footer(text="This is a preview. Click the button below to send submit the observation. Resend the command with correct information if you've made a mistake.")
    await interaction.response.send_message(embed=embed, view=Buttons(), ephemeral=True)

@tree.command(
    name='list-observations',
    description='List observations of a user',
    guild=discord.Object(id=server_id)
)
@app_commands.describe(user="User to view observations for.")
@discord.app_commands.checks.has_any_role(1398653755519537284)
async def listObs(interaction: discord.Interaction, user: discord.Member):
    try:
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        table_name = "o" + str(user.id)
        c.execute(f"SELECT description, date, observation_type FROM {table_name};")
        rows = c.fetchall()
        def emojiPicker(observation):
            if observation == "Positive":
                emoji = "🟢"
                return emoji
            elif observation == "Negative":
                emoji = "🔴"
                return emoji

        observations = [f"- {emojiPicker(observation_type)}`{desc}` - ID:{str(date)} <t:{date}>" for desc, date, observation_type in rows]
        L = 10
        async def get_page(page: int):
            emb = discord.Embed(title=f"Observation list for {user}", description="")
            offset = (page-1) * L
            for obs in observations[offset:offset+L]:
                emb.description += f"{obs}\n"
            emb.set_author(name=f"Requested by {interaction.user}")
            n = Pagination.compute_total_pages(len(observations), L)
            emb.set_footer(text=f"Page {page} from {n}")
            return emb, n
        await Pagination(interaction, get_page).navegate()
    except Exception as e:
        embed = discord.Embed(title="Unknown error occured!", colour=0xc01c28, description=f"```{e}```")
        await interaction.response.send_message(embed=embed)

@tree.command(
    name='view-observation',
    description='View a specific boservation of a user',
    guild=discord.Object(id=server_id)
)
@app_commands.describe(user="User to view an observation for.", obsid="The ID of the observation. Can be found via /list-observations")
@discord.app_commands.checks.has_any_role(1398653755519537284)
async def viewObs(interaction: discord.Interaction, user: discord.Member, obsid: str):
    try:
        embed = discord.Embed(title="Viewing obersvations",
                  colour=0x00b0f4)
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute(f"SELECT * FROM {"o" + str(user.id)} WHERE date = ?", (obsid,)) # reusing observation time in unix time as an id since its unique
        row = c.fetchone()
        if row:
            observation_type = row[0]
            description = row[1]
            time = row[2]
            screenshot = row[3]
            observer = row[4]
            embed = discord.Embed(colour=0xf66151)
            embed.set_author(name=f"{user}\'s observation", icon_url=user.avatar.url)

            embed.add_field(name="Observation type",
                            value=observation_type,
                            inline=True)
            embed.add_field(name="Description",
                            value=description,
                            inline=False)
            embed.add_field(name="Time",
                            value=f"<t:{time}>",
                            inline=False)
            embed.add_field(name="Observer",
                            value=f"<@{observer}>",
                            inline=False)
            
            embed.set_footer(text=f"Observation ID: {obsid}", icon_url=interaction.user.avatar.url)
            embed.set_image(url=screenshot)
            c.close()
            conn.close()
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="Observation not found!", colour=0xc01c28)
            await interaction.response.send_message(embed=embed)
    except sqlite3.OperationalError:
            embed = discord.Embed(title="SQL: Table not found!", colour=0xc01c28, description="This user may not have any observations at all.")
            await interaction.response.send_message(embed=embed)

@tree.command(
    name='delete-observation',
    description='Delete a specific boservation of a user',
    guild=discord.Object(id=server_id)
)
@app_commands.describe(user="User to delete an observation for.", obsid="The ID of the observation. Can be found via /list-observations")
@discord.app_commands.checks.has_any_role(1398653755519537284)
async def deleteObs(interaction: discord.Interaction, user:discord.Member, obsid:str):
        try:
            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            c.execute(f"SELECT * FROM {"o"+str(user.id)} WHERE date = ?", (obsid,))
            row = c.fetchone()
            if row:
                c.execute(f"DELETE FROM {"o"+str(user.id)} WHERE date = ?", (obsid,))
                conn.commit()
                c.close()
                conn.close()
                embed = discord.Embed(title="Observation deleted!",
                          description=f"Observation for {user} (ID: {obsid}) was deleted succesfully!",
                          colour=0x57e389)
                await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title="Observation not found!", colour=0xc01c28)
                await interaction.response.send_message(embed=embed)
        except sqlite3.OperationalError:
                embed = discord.Embed(title="SQL: Table not found!", colour=0xc01c28, description="This user might not have any observations at all!")
                await interaction.response.send_message(embed=embed)

load_dotenv()
token = os.getenv('TOKEN')
bot.run(token)
