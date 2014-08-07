#!/usr/bin/python3
from argparse import ArgumentParser
import sys
import curses
import socket
import json
import time
import datetime
import struct
import minestorm.common.resources
import minestorm.common
import minestorm.console
import minestorm.test

class CommandsManager( minestorm.common.resources.ResourceWrapper ):
    """
    This class manages all cli commands
    """
    resource = 'cli.commands'

    def prepare_parser(self):
        """ Prepare the arguments parser """
        parser = ArgumentParser(prog="minestorm") # Initialize a new ArgumentParser instance
        parser.add_argument('--version', version=minestorm.__version__, action='version')
        subs = parser.add_subparsers(help='commands', dest='command') # Initialize the subparser for the main command
        for name, command in self:
            sub = subs.add_parser(name, help=command.description) # Register the command
            command.boot(sub) # Allow command customization
        return parser

    def route(self):
        """ "Route" a call into the right command """
        parser = self.prepare_parser() # Get the parser
        args = parser.parse_args() # Parse the arguments
        # If a command is provided execute it
        # else show the usage
        if args.command:
            self[args.command].run(args) # Run the command
        else:
            parser.print_usage()

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
            # Create a new socket
            s = socket.socket()
            s.connect(( socket.gethostname(), minestorm.get('configuration').get('networking.port') ))
            # Prepare data
            to_send = json.dumps(data).encode('utf-8')
            length = struct.pack('I', len(to_send))
            # Send the request
            minestorm.common.send_packet(s, length)
            minestorm.common.send_packet(s, to_send)
            # Receive response
            length = struct.unpack('I', minestorm.common.receive_packet( s, 4 ))[0]
            raw = minestorm.common.receive_packet( s, length )
            # Load the response
            response = json.loads(raw.decode('utf-8'))
            # Shutdown the socket
            s.shutdown(socket.SHUT_RD)
            s.close()
            return response
        except socket.error:
            return

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

class StartCommand(Command):
    """
    Command which start a server
    """
    name = 'start'
    description = 'start a server'

    def boot(self, parser):
        parser.add_argument('server', help='choose which server start')

    def run(self, args):
        # Try to get a session id
        sid_request = self.request({ 'status': 'new_session' })
        # If the server is online
        if sid_request:
            # Try to start the server
            request = self.request({ 'status': 'start_server', 'server': args.server, 'sid': sid_request['sid'] })
            if request['status'] == 'failed':
                print('Error: {}'.format(request['reason']), f=sys.stderr)
                exit(1)
        else:
            print('Error: can\'t reach the server', f=sys.stderr)
            exit(1)

class StopCommand(Command):
    """
    Command which stop a server
    """
    name = 'stop'
    description = 'stop a server'

    def boot(self, parser):
        parser.add_argument('server', help='choose which server stop')

    def run(self, args):
        # Try to get a session id
        sid_request = self.request({ 'status': 'new_session' })
        # If the server is online
        if sid_request:
            # Try to stop the server
            request = self.request({ 'status': 'stop_server', 'server': args.server, 'sid': sid_request['sid'] })
            if request['status'] == 'failed':
                print('Error: {}'.format(request['reason']), f=sys.stderr)
                exit(1)
        else:
            print('Error: can\'t reach the server', f=sys.stderr)
            exit(1)

class StartAllCommand(Command):
    """
    Command which start all servers
    """
    name = 'start-all'
    description = 'start all servers'

    def run(self, args):
        # Try to get a session id
        sid_request = self.request({ 'status': 'new_session' })
        # If the server is online
        if sid_request:
            # Try to start all servers
            request = self.request({ 'status': 'start_all_servers', 'sid': sid_request['sid'] })
            if request['status'] == 'failed':
                print('Error: {}'.format(request['reason']), f=sys.stderr)
                exit(1)
        else:
            print('Error: can\'t reach the server', f=sys.stderr)
            exit(1)

class StopAllCommand(Command):
    """
    Command which stop all servers
    """
    name = 'stop-all'
    description = 'stop all servers'

    def run(self, args):
        # Try to get a session id
        sid_request = self.request({ 'status': 'new_session' })
        # If the server is online
        if sid_request:
            # Try to stop all servers
            request = self.request({ 'status': 'stop_all_servers', 'sid': sid_request['sid'] })
            if request['status'] == 'failed':
                print('Error: {}'.format(request['reason']), f=sys.stderr)
                exit(1)
        else:
            print('Error: can\'t reach the server', f=sys.stderr)
            exit(1)

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
