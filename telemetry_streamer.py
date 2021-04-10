import socket
from datetime import datetime
import signal
import sys
import time
import json
import threading
from tinydb import TinyDB, Query

BUFFER_SIZE = 1024

STATE = ('mid', 'x', 'y', 'z', 'mpry',
         'pitch', 'roll', 'yaw',
         'vgx', 'vgy', 'vgz',
         'templ', 'temph',
         'tof', 'h', 'bat', 'baro', 'time',
         'agx', 'agy', 'agz')

def collect_state(state):
    dic = {k: v for k, v in zip(STATE, ['' for _ in STATE])}
    items = state.split(';')
    pairs = tuple(item.split(':') for item in items)
    values = tuple((pair[0].strip(), pair[-1].strip()) for pair in pairs)
    for i in range(len(values)):
        k, v = values[i][0], values[i][1]
        try:
            dic[k] = int(v)
        except:
            try:
                dic[k] = float(v)
            except:
                pass
    return dic

class TelemetryStreamer:
    def __init__(self, save_data=True):
        self.save_data = save_data
     
    def get(self):
        local = ('', 8890)
        remote = ('192.168.10.1', 8889)

        print("TelemetryStreamer.get")
        sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            sck.bind(local)

            out = None

            print("Attempting to connect with drone..")
            attempts = 3
            for i in range(attempts):
                print("Attempt number is " + str(i))
                sck.sendto('command'.encode('utf-8'), remote)
                buffer = sck.recv(BUFFER_SIZE)
                out = buffer.decode('utf-8')

                if out == 'ok':
                    print('accepted')
                    break
                else:
                    print('rejected')
                    time.sleep(0.5)
                    out = None

            db = TinyDB('data/drone_db.json')
            telemetry = db.table("StreamingTelemetry")

            print("Receiving data from drone")
            while out:
                buffer = sck.recv(BUFFER_SIZE)
                out = buffer.decode('utf-8')
                out = out.replace('\n', '')
                # print("out ===>> " + out)
                dic = collect_state(out)
                #print(''.join(str(dic).split(' ')), file=sys.stdout, flush=True)
                if self.save_data:
                    telemetry.insert(dic)
                yield json.dumps(dic)
                time.sleep(1/15.0)
        except Exception as e:
            print(str(e))
        finally:
            sck.close()
           

           
