#!/usr/bin/python3
import logging
import os.path
import json
import minestorm.server.networking
import minestorm.server.requests
import minestorm.server.servers
import minestorm.server.sessions

class MinestormServer:
    """
    The main minestorm server instance
    It saves its instance in MinestormServer.instance, so you can grab it later
    """

    def __init__(self, configuration_directory):
        # Make instance available globally
        global instance
        instance = self
        # Setup configuration
        self._setup_configuration(configuration_directory)
        # Setup logging
        self.logger = logging.getLogger('minestorm')
        self._setup_logging()
        self.logger.info('Starting Minestorm 1.0.0 by Pietro Albini...')
        # Setup the rest
        self._setup_networking()
        self._setup_requests()
        self._setup_servers()
        self._setup_sessions()

    def _setup_configuration(self, configuration_file):
        """ Setup the configuration """
        # For some strange reasons configuration files must exists
        if os.path.exists(configuration_file):
            # Load the configuration from the json file
            f = open(configuration_file, "r")
            self.configuration = json.load(f)
            f.close()
        else:
            raise RuntimeError("Configuration file not found: "+configuration_file)

    def _setup_logging(self):
        """ Setup the logging """
        # Get the logging level
        level = getattr( logging, str(self.configuration['logging']['level']).upper() )
        self.logger.setLevel( level )
        # Prepare the formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # Set the stream handler
        stream = logging.StreamHandler()
        stream.setLevel( level )
        stream.setFormatter( formatter )
        # Register all
        self.logger.addHandler( stream )

    def _setup_networking(self):
        """ Setup the networking """
        self.networking = minestorm.server.networking.Listener()
        self.networking.bind( self.configuration['networking']['port'] ) # Bind the console port
        self.networking.listen() # Listen for connections

    def _setup_requests(self):
        """ Setup request processors """
        self.requests = minestorm.server.requests.RequestSorter()
        self.requests.register( minestorm.server.requests.PingProcessor )
        self.requests.register( minestorm.server.requests.NewSessionProcessor )
        self.requests.register( minestorm.server.requests.RemoveSessionProcessor )
        self.requests.register( minestorm.server.requests.ChangeFocusProcessor )
        self.requests.register( minestorm.server.requests.StartServerProcessor )
        self.requests.register( minestorm.server.requests.StopServerProcessor )
        self.requests.register( minestorm.server.requests.CommandProcessor )
        self.requests.register( minestorm.server.requests.StatusProcessor )
        self.requests.register( minestorm.server.requests.UpdateProcessor )
        # Subscribe for new requests
        self.networking.subscribe( self.requests.sort, {}, 'request' )

    def _setup_servers(self):
        """ Setup the servers manager """
        self.servers = minestorm.server.servers.ServersManager()
        # Register all servers
        for section in self.configuration['available_servers']:
            self.servers.register( section ) # Register the server

    def _setup_sessions(self):
        """ Setup the sessions manager """
        self.sessions = minestorm.server.sessions.SessionsManager()
        # Subscribe for output lines
        self.servers.subscribe(self.sessions.add_line, {}, 'line', 'server')

    def shutdown(self):
        """ Shutdown minestorm """
        self.logger.info('Shutting down minestorm...')
        self.networking.stop() # Stop the networking and close the port
        self.servers.stop_all() # Stop all servers
        self.logger.info('Bye!')

instance = None