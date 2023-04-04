from WS_UMB.WS_UMB import UMBError
from time import time

class Measure:
    def __init__(self, umb, name):
        self.umb = umb
        self.name = name

        self.channels = {
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

    def get(self):
        values = {}

        for _, (identifier, channel) in enumerate(self.channels.items()):
            try:
                value, status = self.umb.onlineDataQuery(channel)
            except UMBError:
                print(f"Error reading value form channel {channel}: {identifier}")
                continue

            if status != 0:
                print(f"Status is not 0 on channel {channel}: {identifier} {self.umb.checkStatus(status)}")
                continue

            values[f"{self.name}[{identifier}]"] = value

        values[f"{self.name}[measured_at]"] = time()
        return values
