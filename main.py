#!/root/meteoselti/venv/bin/python3

from WS_UMB.WS_UMB import WS_UMB
from dotenv import load_dotenv
from measure import Measure
from time import time
import requests
import json
import cv2
import os

class Main:
    def __init__(self, base_url, measure):
        self.base_url = base_url
        self.measure = measure

        load_dotenv()

    def url(self, path):
        if path.startswith("/"):
            return self.base_url + path
        return self.base_url + "/" + path
    
    def get_image(self):
        cap = cv2.VideoCapture(os.getenv("RTSP_URL"), cv2.CAP_FFMPEG)
        return cap.read()
    
    def start(self):
        self.main()

    def main(self):
        headers = { "Authorization": os.getenv("BEARER_TOKEN") }

        values = self.measure.get()
        response = requests.put(self.url("api/create"), headers=headers, data=values)
        id = json.loads(response.text)["id"]
        
        success, image = self.get_image()
        if not success:
            return
        
        temp_file = f"{int(time())}.jpg"

        cv2.imwrite(temp_file, image)

        with open(temp_file, "rb") as image:
            files = {"sky_capture": image}
            requests.post(self.url(f"api/{id}/attach_image"), headers=headers, files=files)
            
        os.remove(temp_file)


if __name__ == "__main__":
    with WS_UMB() as umb:
        Main("http://192.168.1.100:3000", Measure(umb, "measurement")).start()
