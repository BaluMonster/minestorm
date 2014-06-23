#!/usr/bin/python3
import logging
import os.path
import json
import minestorm

class MinestormServer:
    """
    The main minestorm server instance
    """

    def start(self):
        """ Start minestorm server """
        minestorm.get('server.networking').listen()

    def shutdown(self):
        """ Shutdown minestorm server """
        logging.getLogger('minestorm').info('Shutting down minestorm...')
        minestorm.get('server.networking').stop() # Stop the networking and close the port
        minestorm.get('server.servers').stop_all() # Stop all servers
        logging.getLogger('minestorm').info('Bye!')
