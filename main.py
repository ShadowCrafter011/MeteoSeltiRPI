#!/root/meteoselti/venv/bin/python3

from data_manager import DataManager
from WS_UMB.WS_UMB import UMBError
from WS_UMB.WS_UMB import WS_UMB
from dotenv import load_dotenv
from time import time
import requests
import json
import cv2
import os

def main(base_url, umb, name):
    load_dotenv()

    # Instantiate the data manager to start uploading missing data
    data_manager = DataManager(name, base_url)

    headers = {
        "Authorization": os.getenv("BEARER_TOKEN")
    }

    json_headers = headers.copy()
    json_headers["Content-Type"] = "application/json"

    channels = {
        "air_temperature": 100,                     # float
        "dewpoint_temperature": 105,                # float
        "wet_bulb_temperature": 114,                # float
        "wind_chill_temperature": 111,              # float
        "relative_humidity": 200,                   # float
        "absolute_humidity": 205,                   # float
        "humidity_mixing_ratio": 210,               # float
        "relative_air_pressure": 305,               # float
        "absolute_air_pressure": 300,               # float
        "air_density": 310,                         # float
        "specific_enthalpy": 215,                   # float
        "wind_speed": 401,                          # float
        "wind_direction": 501,                      # float
        "wind_direction_corrected": 502,            # float
        "wind_direction_standard_deviation": 503,   # float
        "wind_value_quality": 806,                  # float
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
        print(response.text)
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
        id = json.loads(response.text)["id"]
        temp_file = f"{int(time())}.jpg"
        cv2.imwrite(temp_file, image)

        with open(temp_file, "rb") as image:
            files = {"sky_capture": image}
            requests.post(f"{base_url}/api/upload/image", headers=headers, data={"id": id}, files=files)

        os.remove(temp_file)
    else:
        data_manager.attach_image(data_id, image)

    # Join the upload process
    data_manager.upload_process.join()

if __name__ == "__main__":
    with WS_UMB() as umb:
        main("https://api.meteoselti.ch", umb, "measurement")
