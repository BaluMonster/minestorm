#!/usr/bin/python3
from argparse import ArgumentParser
import sys
import curses
import socket
import json
import time
import datetime
import struct
import shutil
import os
import pkg_resources
import minestorm
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
        parser.add_argument('-c', '--configuration', help='set the configuration file path', dest='_configuration', metavar='PATH', default=None)
        subs = parser.add_subparsers(help='commands', dest='_command') # Initialize the subparser for the main command
        for name, command in self:
            sub = subs.add_parser(name, help=command.description) # Register the command
            command.boot(sub) # Allow command customization
        return parser

    def route(self):
        """ "Route" a call into the right command """
        parser = self.prepare_parser() # Get the parser
        args = parser.parse_args() # Parse the arguments
        # If a configuration file was provided load it
        if args._configuration:
            self._load_configuration(args._configuration)
        # If a command is provided execute it
        # else show the usage
        if args._command:
            self[args._command].run(args) # Run the command
        else:
            parser.print_usage()

    def _load_configuration(self, file_name):
        """ Handler for the -c option """
        # If the path exists load it
        if os.path.exists(file_name):
            minestorm.get('configuration').load(file_name)
        else:
            print('Error: configuration file not found: {}'.format(file_name))
            minestorm.shutdown()

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

    def boot(self, parser):
        parser.add_argument('server', help='choose for which server start the console', nargs='?', default=None)

    def run(self, args):
        try:
            console = minestorm.console.MinestormConsole()
            if args.server:
                if args.server in minestorm.get('console.servers').all():
                    minestorm.get('console.ui').focus = args.server
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
                print('Error: {}'.format(request['reason']), file=sys.stderr)
                exit(1)
        else:
            print('Error: can\'t reach the server', file=sys.stderr)
            exit(1)

class StopCommand(Command):
    """
    Command which stop a server
    """
    name = 'stop'
    description = 'stop a server'

    def boot(self, parser):
        parser.add_argument('server', help='choose which server stop')
        parser.add_argument('-m', '--message', help='message you want to display on stop', default=None)

    def run(self, args):
        # Try to get a session id
        sid_request = self.request({ 'status': 'new_session' })
        # If the server is online
        if sid_request:
            # Try to stop the server
            request = self.request({ 'status': 'stop_server', 'server': args.server, 'message': args.message, 'sid': sid_request['sid'] })
            if request['status'] == 'failed':
                print('Error: {}'.format(request['reason']), file=sys.stderr)
                exit(1)
        else:
            print('Error: can\'t reach the server', file=sys.stderr)
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
                print('Error: {}'.format(request['reason']), file=sys.stderr)
                exit(1)
        else:
            print('Error: can\'t reach the server', file=sys.stderr)
            exit(1)

class StopAllCommand(Command):
    """
    Command which stop all servers
    """
    name = 'stop-all'
    description = 'stop all servers'

    def boot(self, parser):
        parser.add_argument('-m', '--message', help='message you want to display on stop', default=None)

    def run(self, args):
        # Try to get a session id
        sid_request = self.request({ 'status': 'new_session' })
        # If the server is online
        if sid_request:
            # Try to stop all servers
            request = self.request({ 'status': 'stop_all_servers', 'message': args.message, 'sid': sid_request['sid'] })
            if request['status'] == 'failed':
                print('Error: {}'.format(request['reason']), file=sys.stderr)
                exit(1)
        else:
            print('Error: can\'t reach the server', file=sys.stderr)
            exit(1)

class CommandCommand(Command):
    """
    Command which send a command to a server
    """
    name = 'command'
    description = 'send a command to all servers'

    def boot(self, parser):
        parser.add_argument('-s', '--server', help='send only to that server', action='append', dest='servers', default=None, metavar='SERVER')
        parser.add_argument('command', help='the command you want to send')

    def run(self, args):
        # Try to get a session id
        sid_request = self.request({ 'status': 'new_session' })
        # If the server is online
        if sid_request:
            servers = args.servers
            # If the servers list is empty retrieve it
            # from the backend server
            if servers is None:
                status = self.request({ 'status': 'status', 'sid': sid_request['sid'] })
                servers = list(status['servers'].keys()) # Get servers list
            # Send the command to specified servers
            for server in servers:
                response = self.request({ 'status': 'command', 'server': server, 'command': args.command, 'sid': sid_request['sid'] })
                if response['status'] == 'failed':
                    print('Error on {}: {}'.format(server, response['reason']), file=sys.stderr)
        else:
            print('Error: can\'t reach the server', file=sys.stderr)

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

class ConfigureCommand(Command):
    """
    Command which configure minestorm
    """
    name = 'configure'
    description = 'copy configuration files at there locations'

    def run(self, args):
        # Get the content of the default file bundled with setuptools
        content = pkg_resources.resource_string('minestorm', '_samples/configuration.json').decode('utf-8')
        # Get the destination directory
        destination = minestorm.get('configuration').default_file_path()
        # Copy it to its destination
        if not os.path.exists(destination):
            # Create base directories if needed
            os.makedirs( os.path.dirname(destination), exist_ok=True)
            # Save the configuration file
            with open(destination, 'w') as f:
                f.write(content)
            print('The minestorm configuration file is now at {}'.format(destination))
        else:
            print('Error: minestorm: a file already exists at {}'.format(destination))

def main():
    """ CLI entry point """
    minestorm.boot('cli')
    minestorm.get('cli').route()

