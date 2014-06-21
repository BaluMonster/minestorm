#!/usr/bin/python3
import inspect
import minestorm
import minestorm.common
import minestorm.common.configuration
import minestorm.cli

class BaseBooter:
    """
    Class which define a booter
    Must be extended if you want to use it
    """

    name = '__base__'
    dependencies = []

    def __init__(self):
        self._collect_booters() # Collect booters

    def _collect_booters(self, prefix="boot_"):
        """ Collect booters methods (all starting with the prefix) """
        self._collected_methods = []
        # Get all members of self
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        # Iterate over methods
        for name, func in methods:
            # If the method starts with the prefix
            if name.startswith(prefix):
                self._collected_methods.append(func) # Append it to the collected methods list
        self._collected_methods.sort(key=lambda method: method.__name__) # Sort by method name

    def boot(self, manager):
        """ Boot this component """
        # First boot dependencies
        for dependency in self.dependencies:
            manager.boot(dependency)
        # Execute all collected methods
        for method in self._collected_methods:
            method()

class BootManager( minestorm.common.BaseManager ):
    """
    Class which manage all booters
    """
    name_attribute = 'name'
    subclass_of = BaseBooter
    resource_name = 'booter'

    def __init__(self):
        self._booted = []
        super(BootManager, self).__init__()

    def boot(self, component):
        """ Boot a component """
        if component in self:
            # Check if the component wasn't already booted
            if component not in self._booted:
                self[component].boot(self) # Boot it
                self._booted.append(component)
        else:
            raise KeyError("Component not found: {}".format(component))

class GlobalBooter( BaseBooter ):
    """
    Class which boot the global part of minestorm
    """
    name = 'global'

    def boot_1_configuration(self):
        """ Boot configuration """
        manager = minestorm.common.configuration.ConfigurationManager()
        minestorm.bind("configuration", manager)
        # Load configuration
        manager.load("minestorm.json")

class CliBooter( BaseBooter ):
    """
    Class which boot the cli interface of minestorm
    """
    name = 'cli'
    dependencies = ['global']

    def boot_1_cli(self):
        """ Boot the cli """
        manager = minestorm.cli.CommandsManager()
        minestorm.bind("cli", manager)
        # Register commands
        manager.register( minestorm.cli.StartCommand() )
        manager.register( minestorm.cli.ConsoleCommand() )
        manager.register( minestorm.cli.StatusCommand() )
