#!/usr/bin/python3
# This package contains classes and functions used by all the
# minestorm project

class BaseManager:
    """
    This class provides an abstract implementation of the
    manager design pattern
    """
    name_attribute = 'name' # The object attribute which contains the object name (example: object.name)
    subclass_of = object # The object must be a subclass of that object
    resource_name = 'resource' # The name of the resource this class manages

    def __init__(self):
        self._objects = {}

    def __repr__(self):
        return '<{} manager>'.format( self.resource_name.capitalize() )

    def register(self, obj, force=False):
        """ Register an object into the container """
        # Check if the object is an instance or subclass of self.subclass_of
        if isinstance(obj, self.subclass_of):
            # Now check if the object isn't already registered
            name = getattr(obj, self.name_attribute)
            if name not in self._objects or force:
                # Register it
                self._objects[name] = obj
            else:
                raise NameError('The {} {} was already registered'.format(name, self.resource_name))
        else:
            raise RuntimeError('The passed object isn\'t an instance of {} or one of its subclasses'.format(self.subclass_of.__name__))

    def unregister(self, *names):
        """ Unregister some objects from the container """
        # Iterate over arguments
        for name in names:
            # Check if the name is registered
            if name in self._objects:
                del self._objects[name] # Delete the object
            else:
                raise NameError('The {} {} wasn\'t registered'.format(name, self.resource_name))

    def flush(self):
        """ Flush all objects """
        # Unregister all objects
        self.unregister( *self._objects.keys() )

    def __len__(self):
        return len(self._objects)

    def __getitem__(self, name):
        return self._objects[name]

    # __setitem__ and __delitem__ are not implemented because
    # you need to use the register and unregister functions

    def __iter__(self):
        return iter(self._objects.items())

    def __contains__(self, name):
        return name in self._objects