import logging
from threading import *
from websocket_server import WebsocketServer
from threaded_telemetry_streamer import ThreadedTelemetryStreamer

streamer_lock = Semaphore(1)
streamer = None
clients = set()

def new_client(client, server):
    print("new_client: " + str(client))
    global streamer, streamer_lock, clients
    streamer_lock.acquire()
    if streamer == None:
        try:
            streamer = ThreadedTelemetryStreamer(server)
            streamer.start()
            clients.add(client["id"])
        except Exception as e:
            print("Something went wrong in new_client: " + str(e))
            streamer = None
    else:
        clients.add(client["id"])
    streamer_lock.release()

def client_left(client, server):
    print("client_left: " + str(client))
    global streamer, streamer_lock, clients
    streamer_lock.acquire()
    clients.remove(client["id"])
    if len(clients) == 0:
        streamer.stop()
        streamer = None
    streamer_lock.release()

def message_received(client, server, message):
    print(str(client) + '---->' + message)

server = WebsocketServer(13254, host='localhost', loglevel=logging.INFO)
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
server.set_fn_message_received(message_received)

server.run_forever()
