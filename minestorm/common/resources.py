#!/usr/bin/python3
import minestorm

class ResourcesManager:
    """
    This class manages all resources used by minestorm.
    Resources can be commands, request processors and more
    """

    def __init__(self):
        self._resources = {}

    def __repr__(self):
        return '<Resources manager>'

    def add(self, name, subclass_of=object, name_attribute='name', validator=( lambda resource: True )):
        """ Add a new resource """
        # Check if the subclass_of is a class
        if type(subclass_of) != type:
            raise ValueError('You must provide a class as `subclass_of`')
        # Validator must be callable
        if not callable(validator):
            raise ValueError('Validator must be a callable object')
        # Add it only if it isn't in the resources dict
        if name not in self._resources:
            # Create a new resource
            self._resources[name] = Resource(name, subclass_of, name_attribute, validator)
        else:
            raise NameError('A resource with the name {} already exists'.format(name))

    def remove(self, name):
        """ Remove a resource """
        # Remove it only if exists (Doh!)
        if name in self._resources:
            del self._resources[name]
        else:
            raise KeyError('No resource has the name {}'.format(name))

    def exists(self, name):
        """ Check if a resource exists """
        return name in self._resources

    def get(self, name):
        """ Get a resource """
        return self._resources[name]

class Resource:
    """
    Representation of a resource
    """

    def __init__(self, name, subclass_of, name_attribute, validator):
        self.name = name
        self.subclass_of = subclass_of
        self.name_attribute = name_attribute
        self.validator = validator
        self._objects = {} # Objects container

    def __repr__(self):
        return "<Resource manager for '{}'>".format( self.resource_name )

    def register(self, obj, force=False):
        """ Register an object into the resource """
        # Check if the object is an instance or subclass of self.subclass_of
        if isinstance(obj, self.subclass_of):
            # Now check if the object isn't already registered
            name = getattr(obj, self.name_attribute)
            if name not in self._objects or force:
                # Register it
                self._objects[name] = obj
            else:
                raise NameError('The {} {} was already registered'.format(name, self.name))
        else:
            raise RuntimeError('The passed object isn\'t an instance of {} or one of its subclasses'.format(self.subclass_of.__name__))

    def unregister(self, *names):
        """ Unregister some objects from the resource """
        # Iterate over arguments
        for name in names:
            # Check if the name is registered
            if name in self._objects:
                del self._objects[name] # Delete the object
            else:
                raise KeyError('The {} {} wasn\'t registered'.format(name, self.name))

    def flush(self):
        """ Flush all resources """
        # Unregister all objects
        self.unregister( *self._objects.keys() )

    def has(self, name):
        """ Check if a resource is registered """
        return name in self._objects

    def get(self, name):
        """ Get a resource """
        return self._objects[name]

    def __len__(self):
        return len(self._objects)

    def __getitem__(self, name):
        return self.get(name)

    # __setitem__ and __delitem__ are not implemented because
    # you need to use the register and unregister functions

    def __iter__(self):
        return iter(self._objects.items())

    def __contains__(self, name):
        return name in self._objects
