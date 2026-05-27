import asyncio
import hmac
import hashlib
import time
import json
import aiohttp

class Freedcamp:
    def __init__(self, fc_api_key, fc_secret):
        self.fc_api_key = fc_api_key
        self.fc_secret = fc_secret

    async def getId(self, username, app_id):
        timestamp = int(time.time() * 1000)
        hash_bytes = hmac.new(self.fc_secret.encode(), (self.fc_api_key + str(timestamp)).encode(), hashlib.sha1).digest()
        hash_string = hash_bytes.hex()
        params = {
            "api_key": self.fc_api_key,
            "hash": hash_string,
            "timestamp": timestamp,
            "project_id": app_id
        }
        url = "https://freedcamp.com/api/v1/tasks"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    r = await response.json()

                    def getTaskByTitle(tasks):
                        for task in tasks:
                            if task["title"].lower() == username.lower(): 
                                print(f"TASK FOUND")
                                return task
                        return None

                    task = getTaskByTitle(r["data"]["tasks"])
                    if task:
                        print(f"ID: {task['id']}")
                        return task["id"]
                    else:
                        return None
                else:
                    print(f"getId :: {await response.text()}")
    
    async def postComment(self, task_id, contents, app_id):
        timestamp = int(time.time() * 1000)
        hash_bytes = hmac.new(self.fc_secret.encode(), (self.fc_api_key + str(timestamp)).encode(), hashlib.sha1).digest()
        hash_string = hash_bytes.hex()
        url = "https://freedcamp.com/api/v1/comments"

        params = {
            "api_key": self.fc_api_key,
            "hash": hash_string,
            "timestamp": timestamp
        }
        data = {
            "description": contents,
            "app_id": app_id,
            "task_id": task_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"postComment:: {await response.text()}")
                    return None
