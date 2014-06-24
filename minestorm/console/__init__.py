#!/usr/bin/python3
import socket
import curses
import minestorm
import minestorm.console.networking
import minestorm.console.ui
import minestorm.console.commands

class MinestormConsole:
    """
    Manager of the Minestorm console
    """

    def __init__(self):
        minestorm.bind("console", self) # Bind this in the container
        self._init_networking()
        self._init_ui()
        self._init_commands()

    def _init_networking(self):
        """ Initialize the networking """
        # Create the session
        networking = minestorm.console.networking.Session()
        networking.connect(socket.gethostname(), 45342)
        # Create the updater thread
        updater = minestorm.console.networking.UpdaterThread()
        # Bind all things
        minestorm.bind("console.networking", networking)
        minestorm.bind("console.networking.updater", updater)

    def _init_ui(self):
        """ Initialize the UI """
        ui = minestorm.console.ui.Console()
        minestorm.bind("console.ui", ui)

    def _init_commands(self):
        """ Initialize the console manager """
        commands = minestorm.console.commands.CommandsManager()
        commands.register( minestorm.console.commands.SwitchCommand() )
        commands.register( minestorm.console.commands.StartCommand() )
        commands.register( minestorm.console.commands.StopCommand() )
        minestorm.bind("console.commands", commands)

    def start(self):
        """ Start the console """
        minestorm.register_shutdown_function(self.shutdown)
        minestorm.get("console.networking.updater").start()
        minestorm.get("console.ui").loop()

    def shutdown(self):
        """ Stop the console """
        minestorm.get("console.networking.updater").stop = True
        minestorm.get("console.ui").stop = True
        curses.endwin()
