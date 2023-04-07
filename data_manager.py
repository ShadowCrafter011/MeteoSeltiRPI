from multiprocessing import Process
import requests
import json
import cv2
import os

class DataManager:
    def __init__(self, model_name, base_url):
        self.model_name = model_name
        self.base_url = base_url

        self.headers = { "Authorization": os.getenv("BEARER_TOKEN") }

        self.upload_process = Process(target=self.upload)
        self.upload_process.start()

    def path(self, path):
        return os.path.join("/root/meteoselti", path)

    def ping(self):
        try:
            res = requests.get(f"{self.base_url}/api/ping", headers=self.headers)
        except requests.exceptions.ConnectionError:
            return False
        return json.loads(res.text)["success"] == True

    def upload(self):
        # Terminate early if server is not reachable
        if not self.ping():
            return

        json_files = list(filter(lambda f: f.endswith(".json"), os.listdir(self.path("to_upload"))))

        for i in range(min(100, len(json_files))):
            file_path = os.path.join(self.path("to_upload"), json_files[i])

            # Read and parse JSON file
            with open(file_path) as file:
                data = json.loads(file.read())

            # Add model name back to identifiers
            payload = {}
            for _, (identifier, value) in enumerate(data["data"][self.model_name].items()):
                payload[f"{self.model_name}[{identifier}]"] = value

            # Prepare the sky capture
            files = {}
            with open(data["image"], "rb") as image:
                files = {f"{self.model_name}[sky_capture]": image}

                try:
                    res = requests.put(f"{self.base_url}/api/upload/measurement", headers=self.headers, data=payload, files=files)
                except requests.exceptions.ConnectionError:
                    continue

                if res.status_code == 201:
                    os.remove(file_path)
                    os.remove(data["image"])

    def save_snapshot(self, data):
        data = {
            "data": data,
            "image": None
        }
        measured_at = int(data["data"][self.model_name]["measured_at"])

        path = self.path(f"to_upload/{measured_at}.json")
        with open(path, "w") as file:
            file.write(json.dumps(data))

        return measured_at
    
    def attach_image(self, data_id, image):
        image_path = self.path(f"./to_upload/{data_id}.jpg")
        cv2.imwrite(image_path, image)

        json_path = self.path(f"./to_upload/{data_id}.json")
        with open(json_path) as file:
            data = json.loads(file.read())
            data["image"] = image_path

        with open(json_path, "w") as file:
            file.write(json.dumps(data))
