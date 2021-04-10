import socket
from datetime import datetime
import signal
import sys
import time
import json
from threading import *
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

class MiniConsumer(Thread):
    def __init__(self, websocket_server, streamer):
        print("Creating MiniConsumer.")
        Thread.__init__(self)
        self.websocket_server = websocket_server
        self.streamer = streamer
        self.running = False

    def run(self):
        print("Start running MiniConsumer.")
        self.running = True
        while self.running:
            data_point = self.streamer.read()
            self.websocket_server.send_message_to_all(json.dumps(data_point))

    def stop(self):
        print("Stop miniConsumer.")
        self.running = False


class ThreadedTelemetryStreamer(Thread):

    def __init__(self, websocket_server, save_data=True):
        print("Creating ThreadedTelemetryStreamer.")
        Thread.__init__(self)
        self.can_consume = Semaphore(0)
        self.can_produce = Semaphore(1024)
        self.queue = []
        self.save_data = save_data
        self.running = False
        self.mini_consumer = MiniConsumer(websocket_server, self)
        self.mini_consumer.start()

    def read(self):
        self.can_consume.acquire()
        data_point = self.queue.pop(0)
        self.can_produce.release()
        print("read: " + str(data_point))
        return data_point

    def _write(self, data_point):
        self.can_produce.acquire()
        print("write: " + str(data_point))
        self.queue.append(data_point.copy())
        self.can_consume.release()

    def stop(self):
        print("ThreadedTelemetryStreamer.stop()")
        self.mini_consumer.stop()
        self.running = False

    def run(self):
        local = ('', 8890)
        remote = ('192.168.10.1', 8889)

        print("ThreadedTelemetryStreamer.run")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(local)
        sock.setblocking(False)

        try:
            print("Attempting to connect with drone..")
            attempts = 3
            ack = False
            for i in range(attempts):
                try:
                    print("Attempt number is " + str(i))
                    sock.sendto('command'.encode('utf-8'), remote)
                    buffer = sock.recv(BUFFER_SIZE)
                    out = buffer.decode('utf-8')

                    if out == 'ok':
                        print('accepted')
                        ack = True
                        break
                    else:
                        print('rejected')
                        time.sleep(0.5)
                except Exception as e:
                    print("Failed to connect. Retrying...")
                    time.sleep(0.5)
                    pass
                    
            if not ack:
                raise Exception("Failed to connect. Stop trying.")

            db = TinyDB('data/drone_db.json')
            telemetry = db.table("ThreadedStreamingTelemetry")

            print("Receiving data from drone")
            self.running = True
            sock.setblocking(True)
            while self.running:
                ret = sock.recv(BUFFER_SIZE)
                if ret == 0:
                    continue

                if ret == -1:
                    print("Something went wrong when reading the data from socket.")
                    break

                out = ret.decode('utf-8')
                out = out.replace('\n', '')
                # print("out ===>> " + out)
                dic = collect_state(out)
                #print(''.join(str(dic).split(' ')), file=sys.stdout, flush=True)
                if self.save_data:
                    telemetry.insert(dic)
                self._write(dic)
            
        except Exception as e:
            print("Exception in run():" + str(e))
        finally:
            sock.close()
            self.stop()
            print("ThreadedTelemetryStreamer closing the socket")
