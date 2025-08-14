# Rover API wrapper
import requests

def robloxToDiscord(apiKey, guildId, robloxId):
    url = f"https://registry.rover.link/api/guilds/{guildId}/roblox-to-discord/{robloxId}"
    headers = {
        'Authorization': f"Bearer {apiKey}"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            posts = response.json()
            return posts
        else:
            print('Error:', response.status_code)
            print('Response Content:', response.text)
            return None
    except Exception as e:
        return e

def discordToRoblox(apiKey, guildId, discordId):
    url = f"https://registry.rover.link/api/guilds/{guildId}/discord-to-roblox/{discordId}"
    headers = {
        'Authorization': f"Bearer {apiKey}"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            posts = response.json()
            return posts
        else:
            print('Error:', response.status_code)
            print('Response Content:', response.text)
            return None
    except Exception as e:
        return e
