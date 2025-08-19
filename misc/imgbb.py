import base64
import json
import requests

def upload(api_key, imgurl):
    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": api_key,
        "image": imgurl,
        "expiration": 15552000
    }
    res = requests.post(url, payload).json()
    return res
