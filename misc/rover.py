# Rover API wrapper
import aiohttp

async def robloxToDiscord(apiKey, guildId, robloxId):
    url = f"https://registry.rover.link/api/guilds/{guildId}/roblox-to-discord/{robloxId}"
    headers = {
        'Authorization': f"Bearer {apiKey}"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    posts = await response.json()
                    return posts
                else:
                    print('Error:', response.status)
                    print('Response Content:', await response.text())
                    return None
    except Exception as e:
        return e

async def discordToRoblox(apiKey, guildId, discordId):
    url = f"https://registry.rover.link/api/guilds/{guildId}/discord-to-roblox/{discordId}"
    headers = {
        'Authorization': f"Bearer {apiKey}"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    posts = await response.json()
                    return posts
                else:
                    print('Error:', response.status)
                    print('Response Content:', await response.text())
                    return None
    except Exception as e:
        return e

