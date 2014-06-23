#!/usr/bin/python3
import socket
import json
import threading
import logging

class Listener:
    """
    Network listener
    """

    def __init__(self):
        self.socket = None
        self.binded = False
        self.started = False
        self.thread = None
        self.subscribers = []
        self.logger = logging.getLogger('minestorm.networking')

    def bind(self, port):
        """ Bind a port to the socket """
        if self.socket == None and self.binded == False:
            self.binded = True
            # Create the TCP, with reuse addresses socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind the port
            self.socket.bind( ( socket.gethostname(), int(port) ) )
            self.logger.info('Binded port {0}'.format(port))
        else:
            raise RuntimeError('Already initialized socket')

    def listen(self):
        """ Start the listener """
        if self.socket and self.binded == True and self.started == False:
            self.started = True
            self.socket.listen(5) # Start listening
            self.logger.info('Now listening for new connections')
            # Create a new listener thread
            self.thread = ListenerThread(self)
            self.thread.start()
        else:
            raise RuntimeError('Listener already started')

    def stop(self):
        """ Stop the listener """
        if self.started == True or self.binded == True:
            # Reset variables
            self.binded = False
            self.started = False
            # Stop the thread if it was started
            if self.thread:
                self.thread.stop = True
                self.thread = None
            # Shutdown the socket
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
            self.socket = None
            self.logger.info('Networking stopped!')
        else:
            raise RuntimeError('Can\'t stop a stopped server...')

    def subscribe(self, method, args={}, argname='request'):
        """ Subscribe for new requests """
        # Append the subscriber to the list
        self.subscribers.append( { 'method': method, 'args': args, 'argname': argname } )

    # Events called by ListenerThread

    def _on_request_recived(self, conn, addr, data):
        """ Event called by ListenerThread when a new request was recived """
        request = Request(conn, addr, data)
        self.logger.debug('Recived request from {request.address[0]}:{request.address[1]} containing \'{data}\''.format(request=request, data=data.decode("utf-8").strip()))
        # Notify subscribers
        for subscriber in self.subscribers:
            # Call the method
            args = subscriber['args']
            args[subscriber['argname']] = request
            subscriber['method'](**args)

class Request:
    """
    A request representation
    """

    def __init__(self, conn, addr, data):
        self.replied = False
        self.connection = conn
        self.address = addr
        try:
            self.data = json.loads(data.decode("utf-8")) # Decode json request
        # Catch invalid json input
        except ( SyntaxError, ValueError) as e:
            self.data = {}
            self.reply({'status': 'invalid_request', 'reason': 'Invalid JSON: {0!s}'.format(e)}) # Reply invalid_request

    def reply(self, data):
        """ Reply to the request and shutdown the socket """
        if not self.replied:
            self.replied = True
            encoded = json.dumps(data).encode('utf-8') # Prepare the reply
            self.connection.send(encoded) # Send the reply
            # Shutdown the connection
            self.connection.close()
        else:
            raise RuntimeError('Something already replied to this request')

class ListenerThread(threading.Thread):
    """
    This thread will listen to a specific port
    and send all packets to the listener.
    It's in a separated thread because it need a loop
    and I need to continue working after starting the loop
    """

    def __init__(self, listener):
        self.listener = listener
        self.stop = False
        super(ListenerThread, self).__init__()

    def run(self):
        # Stop the loop putting self.stop to false
        while not self.stop:
            try:
                conn, addr = self.listener.socket.accept() # Accept a connection
                data = conn.recv( 4096 ) # Recive the request
                self.listener._on_request_recived(conn, addr, data) # Pass the request to the listener
            except socket.error:
                if self.listener.started:
                    logging.getLogger('minestorm.networking').critical('Socket broken')
                break
