#!/usr/bin/python3
import socket
import curses
import minestorm
import minestorm.console.networking
import minestorm.console.ui
import minestorm.console.commands
import minestorm.console.servers

class MinestormConsole:
    """
    Manager of the Minestorm console
    """

    def __init__(self):
        minestorm.bind("console", self) # Bind this in the container
        self._init_networking()
        self._init_servers()
        self._init_ui()
        self._init_commands()

    def _init_networking(self):
        """ Initialize the networking """
        # Create the session
        networking = minestorm.console.networking.Session()
        networking.connect(socket.gethostname(), 45342)
        # Bind all things
        minestorm.bind("console.networking", networking)

    def _init_servers(self):
        """ Initialize the servers cache """
        servers = minestorm.console.servers.ServersManager()
        syncher = minestorm.console.servers.SyncherThread()
        # Bind all things
        minestorm.bind("console.servers", servers)
        minestorm.bind("console.servers.syncher", syncher)

    def _init_ui(self):
        """ Initialize the UI """
        ui = minestorm.console.ui.Console()
        # It auto binds himself

    def _init_commands(self):
        """ Initialize the console manager """
        # Setup the resource
        validator = lambda resource: resource.name != '__base__'
        minestorm.get('resources').add('console.commands',
                                       subclass_of = minestorm.console.commands.Command,
                                       name_attribute = 'name',
                                       validator = validator )
        # Setup the manager
        commands = minestorm.console.commands.CommandsManager()
        commands.register( minestorm.console.commands.SwitchCommand() )
        commands.register( minestorm.console.commands.StartCommand() )
        commands.register( minestorm.console.commands.StopCommand() )
        minestorm.bind("console.commands", commands)

    def start(self):
        """ Start the console """
        minestorm.register_shutdown_function(self.shutdown)
        minestorm.get("console.servers.syncher").start()
        minestorm.get("console.ui").loop()

    def shutdown(self):
        """ Stop the console """
        minestorm.get("console.servers.syncher").stop = True
        minestorm.get("console.ui").stop = True
        curses.endwin()
