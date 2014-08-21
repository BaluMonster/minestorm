#!/usr/bin/python3
import threading
import time
import minestorm

class SyncError(Exception):
    """
    Error occured during servers synchronization
    """
    pass

class ServersManager:
    """
    This class manages synchronized copies of backend
    servers objects providing them to the console
    """

    def __init__(self):
        self._servers = {}
        self.sync()

    def sync(self):
        """ Sync local copies of the servers objects with the backend """
        new_servers = set() # Set of new servers
        response = minestorm.get('console.networking').request({ 'status': 'status', 'sid': minestorm.get('console.networking').sid })
        # Raise an exception if the servers list was not provided
        if response['status'] != 'status_response':
            raise SyncError('Unable to get servers list')
        # Iterate over received servers to
        for name, informations in response['servers'].items():
            new_servers.add(name) # Append the server name to the synched servers list
            # If the server wasn't loaded create it
            if name not in self._servers:
                self._servers[name] = Server(name)
            # Update server informations
            self._servers[name].update(informations)
        # If there are servers in the servers list not present in the status
        # remove them
        diff = set(self._servers.keys()) - new_servers
        if len(diff) > 0:
            for server in diff:
                del self._servers[name]

    def all(self):
        """ Return all servers loaded """
        return self._servers.copy()

    def get(self, name):
        """ Return an existing server """
        return self._servers[name]

    def exists(self, name):
        """ Return if a server exists """
        return name in self._servers

class Server:
    """
    Representation of a remote server
    """

    def __init__(self, name):
        self.name = name
        self._lines = {}
        self._last_line_identifier = -1
        self._informations = {}

    def update(self, informations):
        """ Update informations about the server """
        old_informations = self._informations.copy()
        # Update every information
        for key, value in informations.items():
            # First check if the key collides with an attribute of the class
            if hasattr(self, key) and key not in old_informations:
                raise SyncError("Key '{}' on server {} collides with an existing attribute".format(key, self.name))
            # After update the object attribute with the new value
            setattr(self, key, value)
            self._informations[key] = value # Copy on the _informations dict
        # After all delete old unused attributes
        diff = set(old_informations.keys()) - set(informations.keys())
        if len(diff) > 0:
            for key in diff:
                delattr(self, key)
                del self._informations[key]

    def retrieve_lines(self, start, stop):
        """ Retrieve a specified amount of lines """
        # Raise an error if the server is not running
        if self.status not in ('STARTING', 'STARTED', 'STOPPING'):
            raise SyncError('Unable to retrieve lines when the server is not running!')
        # Retrieve lines
        response = minestorm.get('console.networking').request({
            'status': 'retrieve_lines', 'start': start, 'stop': stop, 'server': self.name, 'sid': minestorm.get('console.networking').sid
        })
        # Raise an exception if lines are not provided
        if response['status'] != 'retrieve_lines_response':
            raise SyncError('Unable to retrieve lines')
        # Iterate over lines to check them and add to the lines list
        for identifier, line in response['lines'].items():
            identifier = int(identifier) # Convert the identifier to the correct type
            # First check if the line was already downloaded
            if identifier in self._lines:
                continue
            self._lines[identifier] = line
            # Update the last line identifier if it greater than the actual one
            if identifier > self._last_line_identifier:
                self._last_line_identifier = identifier

    def retrieve_last_lines(self):
        """ Retrieve last lines """
        # If this is the first time lines are retrieved retrieve last 10
        # Else retrieve last ones
        if self._last_line_identifier == -1:
            self.retrieve_lines(-10, -1)
        else:
            self.retrieve_lines(self._last_line_identifier, -1)

    def clear_lines_cache(self):
        """ Clear the lines cache """
        self._lines = {}
        self._last_line_identifier = -1

class SyncherThread(threading.Thread):
    """
    Thread which sync the cache
    """

    def __init__(self):
        super(SyncherThread, self).__init__()
        self.stop = False

    def run(self):
        while not self.stop:
            minestorm.get('console.servers').sync()
            minestorm.get('console.ui').sidebar.update() # Update the sidebar
            time.sleep(1)
