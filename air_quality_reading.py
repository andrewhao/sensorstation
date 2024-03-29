import requests
import json
import os

from pms7003 import Pms7003Sensor, PmsSensorException

THERMONOTO_CLOUD_BASE_URL = os.environ.get('THERMONOTO_CLOUD_BASE_URL', '')

class AirQualityReading:
    def __init__(self):
        self.sensor = Pms7003Sensor('/dev/serial0');

    def run(self):
        data = None
        try:
            data = self.sensor.read()
        except PmsSensorException as e:
            print(e)
            raise(e)
        self.report(data)
        self.sensor.close()
    def report(self, data):
        data['device_id'] = os.environ['HOSTNAME']
        response = requests.post(f'{THERMONOTO_CLOUD_BASE_URL}/air_quality_updates', json=data)
        print('Posting with', data)
        print(response)

if __name__ == '__main__':
    AirQualityReading().run()
