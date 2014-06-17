#!/usr/bin/python3
import socket
import threading
import json
import time
import minestorm

class Session:
    """
    A session representation
    """

    def __init__(self):
        self.sid = None
        self.addr = None

    def connect(self, ip, port):
        """ Connect to a minestorm server """
        self.addr = (ip, port) # Define socket connection pair
        self.refresh_sid() # Get a new sid

    def request(self, data):
        """ Make a new request to the server and return the response """
        if self.addr:
            # Create a new socket
            s = socket.socket()
            s.connect(self.addr)
            # Send the request
            s.send(json.dumps(data).encode('utf-8'))
            # Receive response
            raw = s.recv(4096).decode('utf-8')
            response = json.loads(raw)
            # Shutdown the socket
            s.shutdown(socket.SHUT_RD)
            s.close()
            return response
        else:
            raise RuntimeError('You first need to connect')

    def refresh_sid(self):
        """ Refresh the sid """
        # If the sid is present remove it
        if self.sid:
            self.request({ 'status': 'remove_session', 'sid': self.sid })
            self.sid = None
        # Request a new sid
        response = self.request({ 'status': 'new_session' })
        # If a new sid was provided
        if response['status'] == 'session_created':
            self.sid = response['sid'] # Retrieve the sid
        else:
            raise RuntimeError('Unable to get a sid')

class UpdaterThread(threading.Thread):
    """
    Thread which check for updates
    """

    def __init__(self):
        super(UpdaterThread, self).__init__()
        self.stop = False

    def run(self):
        while not self.stop:
            # First check if a connection was estabilished
            if minestorm.get('console.networking').addr:
                response = minestorm.get('console.networking').request({ 'status': 'update', 'sid': minestorm.get('console.networking').sid })
                minestorm.get('console.ui').load_updates(response)
                time.sleep(0.5)
