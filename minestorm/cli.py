#!/usr/bin/python3
from argparse import ArgumentParser
import minestorm.common.resources
import minestorm.console
import minestorm.test
import sys
import curses
import socket
import json
import time
import datetime

class CommandsManager( minestorm.common.resources.ResourceWrapper ):
    """
    This class manages all cli commands
    """
    resource = 'cli.commands'

    def prepare_parser(self):
        """ Prepare the arguments parser """
        parser = ArgumentParser() # Initialize a new ArgumentParser instance
        subs = parser.add_subparsers(help='commands', dest='command') # Initialize the subparser for the main command
        for name, command in self:
            sub = subs.add_parser(name, help=command.description) # Register the command
            command.boot(sub) # Allow command customization
        return parser

    def route(self):
        """ "Route" a call into the right command """
        parser = self.prepare_parser() # Get the parser
        args = parser.parse_args() # Parse the arguments
        self[args.command].run(args) # Run the command

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

    def request(self, data):
        """ Make a request to the server """
        try:
            # Try to connect
            s = socket.socket()
            s.connect(( socket.gethostname(), minestorm.get('configuration').get('networking.port') ))
        except socket.error:
            # if an error occured return none
            return
        else:
            # Send the request
            s.send(json.dumps(data).encode('utf-8'))
            # Receive response
            raw = s.recv(4096).decode('utf-8')
            response = json.loads(raw)
            # Shutdown the socket
            s.shutdown(socket.SHUT_RD)
            s.close()
            return response

class ExecuteCommand(Command):
    """
    Command which execute minestorm server
    """
    name = 'execute'
    description = 'execute internal server'

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
    Command which check the status of minestorm
    """
    name = 'status'
    description = 'see minestorm status'

    def run(self, args):
        # Try to get a session id
        sid_request = self.request({ 'status': 'new_session' })
        # If the server is online
        if sid_request:
            status = self.request({ 'status': 'status', 'sid': sid_request['sid'] })
            # Display the header
            print('Name'.ljust(15), 'Status'.ljust(10), 'Started at'.ljust(16), 'RAM'.ljust(8), 'Uptime', sep="")
            print('-'*79)
            # Display informations about servers
            for name, details in status['servers'].items():
                # Get basic informations about it
                status = details['status']
                # If the server is running display more informations about it
                if details['status'] in ('STARTING', 'STARTED', 'STOPPING'):
                    started_at = time.strftime("%D %H:%M", time.localtime(details['started_at'])) # Prepare started at
                    ram = str( round(details['ram_used'], 2) )+'%'
                    uptime = datetime.timedelta(seconds=details['uptime'])
                else:
                    started_at, ram, uptime = '-', '-', '-'
                # Display informations
                print(name.ljust(15), status.ljust(10), started_at.ljust(16), ram.ljust(8), uptime, sep="")
        else:
            print('Minestorm is currently stopped')

class TestCommand(Command):
    """
    Command which run unit tests
    """
    name = 'test'
    description = 'run unit tests'

    def run(self, args):
        minestorm.test.run()
