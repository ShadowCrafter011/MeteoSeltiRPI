#!/root/meteoselti/venv/bin/python3

from data_manager import DataManager
from WS_UMB.WS_UMB import UMBError
from WS_UMB.WS_UMB import WS_UMB
from solar import get_current_watts
from dotenv import load_dotenv
from alert import alert
from time import time
import requests
import CloudyAI
import signal
import json
import cv2
import sys
import os


def main(base_url, umb, name):
    signal.signal(signal.SIGALRM, sigalrm_handler)
    signal.alarm(295) # Terminate if script takes longer than 4 minutes and 55 seconds to complete

    load_dotenv()

    # print(get_current_watts())

    # Instantiate the data manager to start uploading missing data
    data_manager = DataManager(name, base_url)

    headers = {
        "Authorization": os.getenv("BEARER_TOKEN")
    }

    json_headers = headers.copy()
    json_headers["Content-Type"] = "application/json"

    channels = {
        "air_temperature": 160,                     # float
        "dewpoint_temperature": 170,                # float
        "wet_bulb_temperature": 114,                # float
        "wind_chill_temperature": 111,              # float
        "relative_humidity": 260,                   # float
        "absolute_humidity": 265,                   # float
        "humidity_mixing_ratio": 270,               # float
        "relative_air_pressure": 365,               # float
        "absolute_air_pressure": 360,               # float
        "air_density": 310,                         # float
        "specific_enthalpy": 215,                   # float
        "wind_speed": 480,                          # float
        "max_wind_speed": 440,                      # float
        "wind_direction": 580,                      # float
        "max_wind_direction": 540,                  # float
        "wind_direction_corrected": 502,            # float
        "wind_direction_standard_deviation": 503,   # float
        "wind_value_quality": 805,                  # float
        "compass_heading": 510,                     # float
        "precipitation": 625,                       # float
        "precipitation_intensity": 820,             # float
        "precipitation_type": 700,                  # int
        "rain_drop_volume": 11000,                  # float
        "wind_sensor_heating": 112,                 # float
        "precipitation_sensor_heating": 113,        # float
        "supply_voltage": 10000                     # float
    }

    values = { name: {} }

    for _, (identifier, channel) in enumerate(channels.items()):
        try:
            value, status = umb.onlineDataQuery(channel)
        except UMBError:
            print(f"Error reading value form channel {channel}: {identifier}")
            continue

        if status != 0:
            print(f"Status is not 0 on channel {channel}: {identifier} {umb.checkStatus(status)}")
            continue

        values[name][identifier] = value

    try:
        solar = get_current_watts()
        for _, (grid, value) in enumerate(solar.items()):
            values[name][grid] = value
    except:
        print("Error getting data from Solaredge API")
        


    values[name]["measured_at"] = time()
    payload = json.dumps(values)

    uploaded = False
    try:
        response = requests.put(f"{base_url}/api/upload/measurement", headers=json_headers, data=payload)
        uploaded = True
    except requests.exceptions.ConnectionError:
        pass

    # Save data to disk if it could not be uploaded
    if uploaded and response.status_code != 201:
        print(f"Server responded with {response.status_code}")
        data_id = data_manager.save_snapshot(values)
        uploaded = False
    elif not uploaded:
        print("Server could not be reached")
        data_id = data_manager.save_snapshot(values)

    # Take picture with the webcam
    cap = cv2.VideoCapture(os.getenv("RTSP_URL"), cv2.CAP_FFMPEG)
    success, image = cap.read()
    if not success:
        print("Picture could not be taken")
        return

    if uploaded:
        measurement_id = json.loads(response.text)["id"]
        temp_file = f"{int(time())}.jpg"
        cv2.imwrite(temp_file, image)

        # Make cloud level prediction
        cloud_status, certainty = CloudyAI.predict(temp_file)

        with open(temp_file, "rb") as image:
            files = {"sky_capture": image}
            requests.post(
                f"{base_url}/api/upload/image",
                headers=headers,
                data={
                    "id": measurement_id,
                    "measurement[cloud_status]": cloud_status,
                    "measurement[cloud_status_certainty]": certainty
                },
                files=files
            )

        os.remove(temp_file)
    else:
        data_manager.attach_image(data_id, image)

    # Join the upload process
    data_manager.upload_process.join()

def sigalrm_handler(*_):
    alert(
        "MeteoSelti script terminated",
        "The MeteoSelti script was terminated after execution too more than 295 seconds"
    )
    raise Exception("Script took too long")


if __name__ == "__main__":
    with WS_UMB() as umb:
        url = "https://api.meteoselti.ch"

        if len(sys.argv) > 1:
            url = sys.argv[1]

        main(url, umb, "measurement")
