#!/usr/bin/python3
import sys

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

# Create a new instance of the container
container = Container()

def bind(*args, **kwargs):
    """ Bind an element into the container """
    return container.bind(*args, **kwargs)

def get(*args, **kwargs):
    """ Get an element from the container """
    return container.get(*args, **kwargs)

def has(*args, **kwargs):
    """ Return true if the key is in the container """
    return container.has(*args, **kwargs)

def remove(*args, **kwargs):
    """ Remove the key from the container """
    return container.remove(*args, **kwargs)

def flush(*args, **kwargs):
    """ Flush the container removing all the keys """
    return container.flush(*args, **kwargs)