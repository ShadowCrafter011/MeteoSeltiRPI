from datetime import datetime, timedelta
from dotenv import load_dotenv
from time import time
import requests
import json
import os


def get_current_watts():
    payload = {
        "api_key": os.getenv("SOLAR_EDGE_API_KEY")
    }

    url = f"https://monitoringapi.solaredge.com/site/{os.getenv('SOLAR_EDGE_ID')}/currentPowerFlow"
    response = requests.get(url, params=payload)

    if response.status_code != 200:
        return 0
        
    values = json.loads(response.text)["siteCurrentPowerFlow"]
    mult = 1000 if values["unit"] == "kW" else 1
    return {
        "grid": values["GRID"]["currentPower"] * mult,
        "load": values["LOAD"]["currentPower"] * mult,
        "pv": values["PV"]["currentPower"] * mult
    }


if __name__ == "__main__":
    load_dotenv()
    print(get_current_watts())
