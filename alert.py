from requests.structures import CaseInsensitiveDict
import requests
import os

def alert(title, message):
    try:
        url = "https://api.pushover.net/1/messages.json"
        token = os.getenv("TOKEN")
        user = os.getenv("USER_ID")
        device = os.getenv("DEVICE")
        payload = "token=%s&user=%s&device=%s&title=%s&message=%s" % (token, user, device, title, message)

        headers = CaseInsensitiveDict()
        headers["content-Type"] = "application/x-www-form-urlencoded"

        requests.post(url, data=payload, headers=headers)
    except:
        print("Failed to send alert \"%s\"" % message)