#!/usr/bin/env python3
# =============================================================================
#  IPK25-CHAT: TCP Chat Server (DisplayName change + Inappropriate Message Block)
# -----------------------------------------------------------------------------
#  Authors     : Vacko (xvaculm00)
#                ChatGPT (OpenAI language model) – contributed to regex design,
#                socket programming suggestions, and segmentation testing logic
#  School      : FIT VUT Brno
#  Description : TCP chat server supporting display name change via JOIN
#                and filters inappropriate messages
#  Created     : 07-04-2025
#  Python ver. : 3.12
# =============================================================================

import socket
import threading
import re
from prometheus_client import start_http_server, Counter, Gauge

# Start Prometheus metrics server
start_http_server(8050)
# Define Prometheus metrics
client_count = Gauge('chat_client_count', 'Number of connected clients')
msg_count = Counter('chat_message_count', 'Number of messages sent')

# Regex patterns from protocol grammar
# The patters where created with a help of chatgpt, because the server is not the core of this project and regexes also 
authPattern = re.compile(r"^AUTH\s+([A-Za-z0-9_-]{1,20})\s+AS\s+([!-~]{1,20})\s+USING\s+([A-Za-z0-9_-]{1,128})\r\n$")
joinPattern = re.compile(r"^JOIN\s+([A-Za-z0-9_-]{1,20})\s+AS\s+([!-~]{1,20})\r\n$")
msgPattern = re.compile(r"^MSG FROM\s+([!-~]{1,20})\s+IS\s+(.{1,60000})\r\n$", re.DOTALL)
byePattern = re.compile(r"^BYE FROM\s+([!-~]{1,20})\r\n$")

# bad_words, idea is that when the server get them, it will sent and error. This way u can test the recieving of error packet.
bad_words = {"recverr", "test123"}

# segmentation words, these words are used to force a segmentation by a server
seg_words = {"reqseg", "seg"}

# only nondefault and default are allowrd 
rooms = {}
roomLock = threading.Lock()

class ChatClient:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.userId = None
        self.displayName = None
        self.room = None
        self.isAuth = False

    def send(self, msg):
        try:
            self.conn.sendall(msg.encode('utf-8'))
        except:
            pass



# Broadcast sends a message to all clients in the same room
def broadcast_segmentation(sender, msg, chunk_size=5, delay=2):
    import time
    if isinstance(msg, str):
        msg = msg.encode('utf-8')

    with roomLock:
        for c in rooms.get(sender.room, []):
            if c.conn != sender.conn:
                print(f"Sending to {c} in chunks with {delay}s delay")  # debug line
                for i in range(0, len(msg), chunk_size):
                    try:
                        chunk = msg[i:i + chunk_size]
                        print(f"Sending chunk: {chunk}")  # debug
                        c.conn.sendall(chunk)
                        time.sleep(delay)
                    except Exception as e:
                        print(f"Failed to send to {c}: {e}")


def broadcast(sender, msg):
    with roomLock:
        for c in rooms.get(sender.room, []):
            if c.conn != sender.conn:
                c.send(msg)

def handleClient(conn, addr):
    client = ChatClient(conn, addr)
    buffer = ""

    try:
        # the main loop of the program
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buffer += data.decode('utf-8')

            # this condition is mandatory, otherwise the packet is not complete
            while "\r\n" in buffer:
                line, buffer = buffer.split("\r\n", 1)
                line += "\r\n"

                # AUTH handling
                if not client.isAuth:
                    match = authPattern.match(line)
                    if match:
                        client.userId, client.displayName, secret = match.groups()
                        if secret == "password": # the password i choose for correct implementation 
                            client.isAuth = True
                            client.room = "default"
                            with roomLock:
                                rooms.setdefault("default", []).append(client)
                            client.send("REPLY OK IS Authentication successful\r\n")
                            broadcast(client, f"MSG FROM SERVER IS {client.displayName} joined default\r\n")
                            client_count.inc()
                        else:
                            client.send("REPLY NOK IS Authentication failed\r\n")
                    else:
                        client.send("ERR FROM UNKNOWN IS Invalid AUTH format\r\n")
                    continue

                # join
                joinMatch = joinPattern.match(line)
                if joinMatch:
                    chanId, new_dname = joinMatch.groups()
                    if chanId not in ["default", "nondefault"]:
                        client.send("REPLY NOK IS Join failed: Unexisting room\r\n")
                        continue
                    with roomLock:
                        if client.room and client in rooms.get(client.room, []):
                            rooms[client.room].remove(client)
                        client.room = chanId
                        client.displayName = new_dname
                        rooms.setdefault(chanId, []).append(client)
                    client.send("REPLY OK IS Join success\r\n")
                    broadcast(client, f"MSG FROM SERVER IS {client.displayName} joined {chanId}\r\n")
                    continue
                # msg
                msgMatch = msgPattern.match(line)
                if msgMatch:
                    dname, content = msgMatch.groups()
                    if dname != client.displayName:
                        client.send(f"ERR FROM {client.displayName} IS Display name mismatch\r\n")
                        continue
                    if any(bad_word in content.lower() for bad_word in bad_words):
                        client.send(f"ERR FROM {client.displayName} IS Inappropriate message\r\n")
                        continue

                    if any(seg_word in content.lower() for seg_word in seg_words):
                        broadcast_segmentation(client, f"MSG FROM {dname} IS {content}\r\n")
                        continue
                    broadcast_segmentation(client, f"MSG FROM {dname} IS {content}\r\n")
                    continue

                # bye
                byeMatch = byePattern.match(line)
                if byeMatch:
                    dname = byeMatch.group(1)
                    if dname != client.displayName:
                        client.send(f"ERR FROM {client.displayName} IS Display name mismatch\r\n")
                        continue
                    broadcast(client, f"MSG FROM SERVER IS {client.displayName} left the chat\r\n")
                    return

                # Anything else = malformed
                client.send(f"ERR FROM {client.displayName} IS Invalid message format\r\n")

    finally:
        # we need to remove the client from the room
        with roomLock:
            if client.room and client in rooms.get(client.room, []):
                rooms[client.room].remove(client)
                client_count.dec()
        conn.close()

def runServer(host='127.0.0.1', port=4596):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"IPK25-CHAT TCP Server listening on {host}:{port}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handleClient, args=(conn, addr), daemon=True).start()

if __name__ == '__main__':
    runServer()
