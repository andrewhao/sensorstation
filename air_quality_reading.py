import requests
from pms7003 import Pms7003Sensor, PmsSensorException

class AirQualityReading:
    def __init__(self):
        self.sensor = Pms7003Sensor('/dev/serial0');
        self.data = None

    def run(self):
        self.data = self.sensor.read()
        self.report(data)
        self.sensor.close()

    def report(self, data):
        data['device_id'] = os.environ['HOSTNAME']
        response = requests.post('http://thermonoto.herokuapp.com/air_quality_updates', data=data)
        print('Posting with', data)
        print(response)

if __name__ == '__main__':
    AirQualityReading().run()