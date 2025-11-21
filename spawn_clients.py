# spawn_clients.py
import socketio
import time
import threading

SERVER = 'http://localhost:5000'
CLIENTS = 60
match_id = 'match-1'
sport = 'cricket'

sockets = []

def make_client(i):
    sio = socketio.Client(logger=False, engineio_logger=False, reconnection=False)

    @sio.event
    def connect():
        # subscribe immediately
        sio.emit('match:subscribe', {'match_id': match_id, 'sport': sport, 'simulate': True})

    @sio.on('match:update')
    def on_update(data):
        # minimal logging to avoid flooding console
        if i < 2:
            print(f"[client {i}] update at {time.strftime('%X')}: {data['id']}")

    @sio.event
    def disconnect():
        pass

    try:
        sio.connect(SERVER, transports=['websocket'])
        sockets.append(sio)
    except Exception as e:
        print("Failed to connect client", i, e)

# spawn clients quickly
threads = []
for i in range(CLIENTS):
    t = threading.Thread(target=make_client, args=(i,), daemon=True)
    t.start()
    threads.append(t)
    time.sleep(0.05)  # slight stagger

# keep main alive to hold clients
print(f"Spawned ~{CLIENTS} clients. Press Ctrl+C to stop.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Disconnecting clients...")
    for s in sockets:
        try:
            s.disconnect()
        except:
            pass
