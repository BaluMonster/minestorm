#!/usr/bin/python3
import subprocess
import threading
import os
import logging
import time
import minestorm

class ServersManager:
    """ Manager of all servers """

    def __init__(self):
        self.servers = {}
        self.logger = logging.getLogger('minestorm.servers')
        self.subscribers = []

    def register(self, details):
        """ Register a new server """
        # Don't insert duplicate servers
        if details['name'] not in self.servers:
            # Allow only bungeecord and minecraft servers
            if details['type'] in ('vanilla', 'bukkit', 'spigot', 'bungeecord'):
                # Create the server
                self.servers[details['name']] = Server(details, self)
                self.logger.debug('Registered server {0}'.format(details['name']))
            else:
                raise RuntimeError('Invalid server type: {0}'.format(details['type']))
        else:
            raise RuntimeError('Server already exists: {0}'.format(details['name']))

    def start_all(self):
        """ Start all servers """
        for name, server in self.servers.items():
            # Start the server only if it isn't already started
            if server.status in (server.STATUS_STOPPED, server.STATUS_CRASHED):
                server.start()

    def stop_all(self):
        """ Stop all servers """
        for name, server in self.servers.items():
            # Stop the server only if it's started
            if server.status == server.STATUS_STARTED:
                server.stop()

    def get(self, name):
        """ Get a server """
        if name in self.servers:
            return self.servers[name]
        else:
            raise NameError('Server {} not found'.format(name))

    def subscribe(self, method, args={}, line_name='line', server_name='server'):
        """ Subscribe for the output """
        # Append the subscriber to the list
        self.subscribers.append( { 'method': method, 'args': args, 'line_name': line_name, 'server_name': server_name } )

    def status(self):
        """ Get the status of all servers """
        result = {}
        # Get the status of all servers
        for name, server in self.servers.items():
            result[name] = server.server_status()
        return result

    def _emit_line(self, server, line):
        """ Emit a line to subscribers """
        for subscriber in self.subscribers:
            # Call the method
            args = subscriber['args']
            args[subscriber['line_name']] = line
            args[subscriber['server_name']] = server
            subscriber['method'](**args)

class Server:
    """ Representation of a process """
    
    # Status codes
    STATUS_STOPPED = 'STOPPED'
    STATUS_STOPPING = 'STOPPING'
    STATUS_STARTED = 'STARTED'
    STATUS_STARTING = 'STARTING'
    STATUS_CRASHED = 'CRASHED'
    
    def __init__(self,  details, manager):
        self.manager = manager
        self.logger = logging.getLogger('minestorm')
        self.details = details
        self.process = None
        self.pipes = {'in': None, 'out': None}
        self.pid = None
        self.output = []
        self.subscribers = []
        self.watcher = None
        self.updater = None
        self.change_status(self.STATUS_STOPPED, True)
        self.started_at = None
        self.ram = None

    def start(self):
        """ Start the server """
        # Allow starting the server only when it's stopped or crashed
        if self.status in (self.STATUS_STOPPED, self.STATUS_CRASHED):
            self.change_status(self.STATUS_STARTING) # Move the status to starting
            try:
                # Generate the command
                command = 'java'
                if 'ram' in self.details['start_command']:
                    if 'min' in self.details['start_command']['ram']:
                        command += ' -Xms'+str(self.details['start_command']['ram']['min'])
                    if 'max' in self.details['start_command']['ram']:
                        command += ' -Xmx'+str(self.details['start_command']['ram']['max'])
                command += ' -jar '+str(self.details['start_command']['jar'])
                if self.details['type'] == 'vanilla':
                    command += ' nogui'
                if 'flags' in self.details:
                    command += ' '+flags
                # Setup process options
                options = {}
                options['shell'] = True
                options['stderr'] = subprocess.STDOUT
                options['stdout'] = subprocess.PIPE
                options['stdin'] = subprocess.PIPE
                # Setup server directory
                if 'directory' in self.details:
                    options['cwd'] = self.details['start_command']['directory']
                else:
                    # If a directory is not passed as detail assume
                    # the jar directory as server directory
                    options['cwd'] = os.path.dirname( self.details['start_command']['jar'] )
                # Start the process
                self.process = subprocess.Popen(command, **options)
                self.change_status(self.STATUS_STARTED)
            except OSError:
                self.change_status(self.STATUS_CRASHED)
                raise RuntimeError('Unable to start the server')
            else:
                # Populate informations
                self.pid = self.process.pid
                self.pipes = {'in': self.process.stdin, 'out': self.process.stdout}
                self.output = []
                self.watcher = OutputWatcher(self) # Create an output watcher
                self.watcher.start()
                self.updater = UsageInformationsUpdater(self)
                self.updater.start()
                self.started_at = time.time() # Set the started at value
        else:
            raise RuntimeError('The server was already started')

    def stop(self):
        """ Stop the server """
        # If the server is running
        if self.status == self.STATUS_STARTED:
            self.change_status(self.STATUS_STOPPING) # Move the status to stopping
            command = ''
            # Minecraft/Bukkit/Spigot and Bungeecord have different stop commands
            if self.details['type'] in ( 'vanilla', 'bukkit', 'spigot' ):
                command += 'stop'
            elif self.details['type'] == 'bungeecord':
                command += 'end'
            # Add the specified stop message or the default stop message
            if 'stop_message' in self.details:
                command += ' '+self.details['stop_message']
            else:
                command += ' Server ran with MineStorm by Pietro Albini'
            # Run the command
            self.command(command) # Run the stop command
        else:
            raise RuntimeError('The server must be started before stopping it')

    def command(self, command):
        """ Send a command to the server """
        # Allow sending commands only when the status is starting, started or stopping
        if self.status in (self.STATUS_STARTING, self.STATUS_STARTED, self.STATUS_STOPPING):
            command += "\n" # Add a break line
            encoded = command.encode("utf-8") # Convert the command to bytes
            # Send the command
            self.pipes['in'].write(encoded)
            self.pipes['in'].flush()
        else:
            raise RuntimeError('The server must be alive to send a command')

    def change_status(self, status, hide=False):
        """ Change the status """
        self.status = status
        if not hide:
            self.logger.info('Changed status of the server {0} to {1}'.format(self.details['name'], status))

    def server_status(self):
        """ Get the status of the server """
        result = {}
        result['status'] = self.status
        # Provide more informations only if the server is running
        if self.status in ( self.STATUS_STARTING, self.STATUS_STARTED, self.STATUS_STOPPING ):
            result['started_at'] = self.started_at
            result['uptime'] = time.time() - self.started_at
            result['ram_used'] = self.ram
        return result

    # Events called by the OutputWatcher

    def _on_line_printed(self, line):
        """ Method called when a line is printed """
        self.output.append(line) # Append the line to the output
        self.manager._emit_line(self.details['name'], line) # Notify subscribers

    def _on_stop(self):
        """ Method called when a server is stopped """
        self.change_status(self.STATUS_STOPPED) # Move the status to stopped
        # Reset informations
        self.watcher.stop = True
        self.watcher = None
        self.updater.stop = True
        self.updater = None
        self.process = None
        self.pipes = {'in': None, 'out': None}
        self.pid = None
        self.output = []
        self.started_at = None
        self.ram = None

    # Proc parser methods

    def _update_resource_usage(self):
        """ Update resource usage variables """
        self.ram = self._parse_ram()

    def _parse_ram(self):
        """ Get ram usage from the proc filesystem """
        result = 0
        procfile = '/proc/{}/status'.format(self.pid) # Prepare file name
        meminfo = '/proc/meminfo'
        # To get the ram usage from the proc file we need to
        # sum 'VmRSS' and 'VmPSS'
        # Also we need to strip the kB suffix from values
        # in order to convert string to int
        with open(procfile, 'r') as f:
            # Iterate over proc file lines
            for line in f:
                # Clean key and value
                key, value = line.split(':')
                key = key.strip()
                value = value.strip()
                # Check if the first two chars are 'Vm'; see above
                if key in ('VmRSS', 'VmPSS'):
                    # Add this value to the result
                    result += int( value.replace('kB', '').strip() )
        # Now we need to get the total ram available, via /proc/meminfo
        with open(meminfo, 'r') as f:
            # Iterate over lines
            for line in f:
                key, value = line.split(':')
                key = key.strip()
                value = value.replace('kB', '').strip()
                # Check if the key is MemTotal
                if key == 'MemTotal':
                    total = int(value)
                    break
        # Calculate usage average
        average = ( result * 100 ) / total
        return average

    # Some magic methods

    def __repr__(self):
        return '<Server "'+self.details['name']+'">'

class OutputWatcher(threading.Thread):
    """ This class simply watch for new output on a server' stdout """

    def __init__(self, server):
        super(OutputWatcher, self).__init__() # Run the parent constructor
        self.server = server
        self.line = ''
        self.stop = False

    def run(self):
        while not self.stop:
            # Get a char from the stdout of the server
            # and convert it to string
            char = self.server.pipes['out'].read(1)
            char = char.decode('utf-8')
            # If the char is empty, the server was stopped
            if char == '':
                self.server._on_stop() # Tell the server that it was stopped
            # If the char is a return char, send the current line to the server
            elif char == '\n':
                self.server._on_line_printed( self.line )
                self.line = '' # Reset the line
            else:
                self.line += char

class UsageInformationsUpdater(threading.Thread):
    """ This thread will update informations about resouces usages for each server """

    def __init__(self, server):
        super(UsageInformationsUpdater, self).__init__() # Run the parent constructor
        self.server = server
        self.stop = False

    def run(self):
        while not ( self.stop or minestorm.shutdowned ):
            # Call the server _update_resource_usage method
            self.server._update_resource_usage()
            # Now sleep a little
            time.sleep( minestorm.get('configuration').get('servers.update_usage_informations_every') )
