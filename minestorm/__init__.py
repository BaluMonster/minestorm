#!/usr/bin/python3
import sys
import signal
import minestorm._boot

__version__ = '1.0.0-alpha1'

class Container:
    """
    The container is a class which collect all useful instances
    """

    def __init__(self):
        self._items = {}

    def bind(self, key, value, force=False):
        """ Bind an element into the container """
        # If the key isn't in the container yet or force is True 
        if key not in self._items or force:
            self._items[key] = value # Bind the item in the container
        else:
            raise KeyError("Key {} already in the container".format(key))

    def get(self, key, default=None):
        """ Get an element from the container """
        # Return the key if is present in the container
        if key in self._items:
            return self._items[key]
        else:
            # If the default isn't none, return it
            # Else raise an exception
            if default != None:
                return default
            else:
                raise KeyError("Key {} not in the container".format(key))

    def has(self, key):
        """ Return true if the key is in the container """
        return key in self._items

    def remove(self, key):
        """ Remove the key from the container """
        # Remove the key only if it's present in the container
        if key in self._items:
            del self._items[key]
        else:
            raise KeyError("Key {} not in the container".format(key))

    def flush(self):
        """ Flush the container removing all the keys """
        self._items = {} # Simply remove all

shutdowned = False

def shutdown():
    """ Shutdown minestorm """
    global shutdowned
    # Execute all shutdown functions
    get('events').trigger('core.shutdown')
    shutdowned = True

# Shutdown correctly when SIGINT is recived
def stop_handler(*args):
    """ Called when SIGINT is sent """
    shutdown()

signal.signal(signal.SIGINT, stop_handler)

# Create a new instance of the container
_container = Container()

# Some shortcuts to the container
bind = _container.bind
get = _container.get
has = _container.has
remove = _container.remove
flush = _container.flush

# Setup the booter
_booter = minestorm._boot.BootManager()
_booter.register( minestorm._boot.GlobalBooter() )
_booter.register( minestorm._boot.CliBooter() )
_booter.register( minestorm._boot.ServerBooter() )

boot = _booter.boot

boot('global') # Boot global part of minestorm

# Register shutdown events
get('events').create('core.shutdown')
