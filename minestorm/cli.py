#!/usr/bin/python3
from argparse import ArgumentParser
import minestorm.console
import curses

class CommandsManager:
    def __init__(self):
        """ Initalize commands manager """
        self.commands = {}

    def register(self, command):
        """ Register a new command """
        if issubclass(command.__class__, Command): # Accept only subclasses of Command
            if command.name != '__base__' and command.name not in self.commands: # Prevent registering of __base__ command or duplicates
                self.commands[command.name] = command # Register the command
            else:
                raise RuntimeError('Invalid command')
        else:
            raise RuntimeError('Invalid command')

    def prepare_parser(self):
        """ Prepare the arguments parser """
        parser = ArgumentParser() # Initialize a new ArgumentParser instance
        subs = parser.add_subparsers(help='commands', dest='command') # Initialize the subparser for the main command
        for command in self.commands.values():
            sub = subs.add_parser(command.name, help=command.description) # Register the command
            command.boot(sub) # Allow command customization
        return parser

    def route(self):
        """ "Route" a call into the right command """
        parser = self.prepare_parser() # Get the parser
        args = parser.parse_args() # Parse the arguments
        self.commands[args.command].run(args) # Run the command

class Command:
    name = '__base__'
    description = 'a command'

    def __new__(cls, *args, **kwargs):
        # Overwrite the class creator to deny
        # instance creation of the base processor
        if cls.name == '__base__':
            raise RuntimeError('Can\'t create instances of the base command')
        else:
            return super(Command, cls).__new__(cls, *args, **kwargs)

    def boot(self, parser):
        """ Boot the command """
        pass

    def run(self, args):
        """ Run the command """
        pass

class StartCommand(Command):
    """
    Command which start minestorm server
    """
    name = 'start'
    description = 'start minestorm internal server'

    def boot(self, parser):
        parser.add_argument('-c', '--conf', help='specify the configuration file path', default='minestorm.json', metavar='PATH', dest='config')

    def run(self, args):
        minestorm.boot('server')
        minestorm.get('server').start()

class ConsoleCommand(Command):
    """
    Command which start the console
    """
    name = 'console'
    description = 'start the console'

    def run(self, args):
        try:
            console = minestorm.console.MinestormConsole()
            console.start()
        finally:
            curses.endwin()

class StatusCommand(Command):
    """
    Command which start the console
    """
    name = 'status'
    description = 'see minestorm status'

    def run(self, args):
        pass
