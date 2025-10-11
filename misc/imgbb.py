import aiohttp
import json

async def upload(api_key, imgurl):
    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": api_key,
        "image": imgurl,
        "expiration": 15552000
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as response:
            res = await response.json()
            return res
