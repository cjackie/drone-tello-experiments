import socket
import sys
import signal
import time

BUFFER_SIZE = 1024

def recv(sock):
    buffer = sock.recv(BUFFER_SIZE)
    out = buffer.decode('utf-8')
    if out != "ok":
        raise "Failed to receive a message"

    print("receiving: " + out)

def sendto(sock, remote, cmd):
    print("cmd: " + cmd)
    sock.sendto(cmd.encode('utf-8'), remote)

if __name__ == '__main__':
    print("commanding...")

    local = ('', 8889)
    remote = ('192.168.10.1', 8889)

    signal.signal(signal.SIGINT, signal.SIG_DFL)

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

        sock.setblocking(True)

        # commands
        sendto(sock, remote, "takeoff")
        recv(sock)
        time.sleep(3.5)

        sendto(sock, remote, "rc 0 0 0 30")
        recv(sock)
        time.sleep(7.5)

        sendto(sock, remote, "rc 0 0 0 -30")
        recv(sock)
        time.sleep(7.5)

        # sendto(sock, remote, "rc 0 0 5 0")
        # recv(sock)
        # time.sleep(3.5)

        # sendto(sock, remote, "rc 0 0 -15 0")
        # recv(sock)
        # time.sleep(3.5)

        sendto(sock, remote, "land")
        recv(sock)
        time.sleep(3.5)

    except Exception as e:
        sendto(sock, remote, "land")
        print("Exception in run():" + str(e))
    finally:
        sock.close()
        print("closing the socket")



