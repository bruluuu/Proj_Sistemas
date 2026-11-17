import socket
import threading
import time

SERVERS = [
    ("server1", 5555),
    ("server2", 5555),
    ("server3", 5555)
]

server_index = 0
index_lock = threading.Lock()

def get_next_server():
    global server_index
    with index_lock:
        s = SERVERS[server_index]
        server_index = (server_index + 1) % len(SERVERS)
        return s

def forward(source, destination):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            destination.sendall(data)
    except:
        pass
    finally:
      try:
          source.close()
      except:
          pass
      try:
          destination.close()
      except:
          pass

def handle_client(client_socket):
    target = None
    for _ in range(len(SERVERS)):
        HOST, PORT = get_next_server()
        try:
            target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target.settimeout(3.0)
            target.connect((HOST, PORT))
            target.settimeout(None)
            break
        except:
            if target:
                target.close()
            target = None
            time.sleep(0.1)

    if not target:
        client_socket.close()
        return

    t1 = threading.Thread(target=forward, args=(client_socket, target), daemon=True)
    t2 = threading.Thread(target=forward, args=(target, client_socket), daemon=True)
    t1.start()
    t2.start()

def pubsub_proxy():
    import zmq
    ctx = zmq.Context()
    xsub = ctx.socket(zmq.XSUB)
    xsub.bind("tcp://*:5557")
    xpub = ctx.socket(zmq.XPUB)
    xpub.bind("tcp://*:5558")
    zmq.proxy(xsub, xpub)

def main():
    threading.Thread(target=pubsub_proxy, daemon=True).start()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 5555))
    server.listen(128)

    while True:
        client_sock, _ = server.accept()
        threading.Thread(target=handle_client, args=(client_sock,), daemon=True).start()

if __name__ == "__main__":
    main()