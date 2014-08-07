#!/usr/bin/python3
import inspect
import logging
import minestorm
import minestorm.common
import minestorm.common.configuration
import minestorm.common.resources
import minestorm.cli
import minestorm.server
import minestorm.server.networking
import minestorm.server.requests
import minestorm.server.servers
import minestorm.server.sessions

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

    def boot_2_resources(self):
        """ Boot the resources manager """
        manager = minestorm.common.resources.ResourcesManager()
        minestorm.bind("resources", manager)

class CliBooter( BaseBooter ):
    """
    Class which boot the cli interface of minestorm
    """
    name = 'cli'
    dependencies = ['global']

    def boot_1_cli(self):
        """ Boot the cli """
        # Setup the resource
        validator = lambda resource: resource.name != '__base__'
        minestorm.get('resources').add('cli.commands',
                                       subclass_of = minestorm.cli.Command,
                                       name_attribute = 'name',
                                       validator = validator )
        # Setup the manager
        manager = minestorm.cli.CommandsManager()
        minestorm.bind("cli", manager)
        # Register commands
        manager.register( minestorm.cli.ExecuteCommand() )
        manager.register( minestorm.cli.StartCommand() )
        manager.register( minestorm.cli.StopCommand() )
        manager.register( minestorm.cli.StartAllCommand() )
        manager.register( minestorm.cli.StopAllCommand() )
        manager.register( minestorm.cli.CommandCommand() )
        manager.register( minestorm.cli.ConsoleCommand() )
        manager.register( minestorm.cli.StatusCommand() )
        manager.register( minestorm.cli.TestCommand() )

class ServerBooter( BaseBooter ):
    """
    Class which boot minestorm server
    """
    name = 'server'
    dependencies = ['global']

    def boot_1_logging(self):
        """ Boot the logging system """
        logger = logging.getLogger('minestorm')
        # Get the logging level
        level = getattr( logging, str(minestorm.get('configuration').get('logging.level')).upper() )
        logger.setLevel( level )
        # Prepare the formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # Set the stream handler
        stream = logging.StreamHandler()
        stream.setLevel( level )
        stream.setFormatter( formatter )
        # Register all
        logger.addHandler( stream )

    def boot_2_networking(self):
        """ Boot the networking """
        manager = minestorm.server.networking.Listener()
        minestorm.bind('server.networking', manager)
        # Bind the console port
        manager.bind( minestorm.get('configuration').get('networking.port') )

    def boot_3_requests(self):
        """ Boot the requests parser """
        # Setup the resource
        validator = lambda resource: resource.name != '__base__'
        minestorm.get('resources').add('server.request_processors',
                                       subclass_of = minestorm.server.requests.BaseProcessor,
                                       name_attribute = 'name',
                                       validator = validator )
        # Create the sorter
        manager = minestorm.server.requests.RequestSorter()
        minestorm.bind('server.requests', manager)
        # Register differend requests
        manager.register( minestorm.server.requests.PingProcessor() )
        manager.register( minestorm.server.requests.NewSessionProcessor() )
        manager.register( minestorm.server.requests.RemoveSessionProcessor() )
        manager.register( minestorm.server.requests.ChangeFocusProcessor() )
        manager.register( minestorm.server.requests.StartServerProcessor() )
        manager.register( minestorm.server.requests.StopServerProcessor() )
        manager.register( minestorm.server.requests.StartAllServersProcessor() )
        manager.register( minestorm.server.requests.StopAllServersProcessor() )
        manager.register( minestorm.server.requests.CommandProcessor() )
        manager.register( minestorm.server.requests.StatusProcessor() )
        manager.register( minestorm.server.requests.UpdateProcessor() )
        # Subscribe for new requests
        minestorm.get('server.networking').subscribe( manager.sort, {}, 'request' )

    def boot_4_servers(self):
        """ Boot the servers manager """
        manager = minestorm.server.servers.ServersManager()
        minestorm.bind('server.servers', manager)
        # Register all servers
        for section in minestorm.get('configuration').get('available_servers'):
            manager.register( section ) # Register the server

    def boot_5_sessions(self):
        """ Boot the sessions manager """
        manager = minestorm.server.sessions.SessionsManager()
        minestorm.bind('server.sessions', manager)
        # Subscribe for output lines
        minestorm.get('server.servers').subscribe(manager.add_line, {}, 'line', 'server')

    def boot_6_manager(self):
        """ Boot the server manager """
        manager = minestorm.server.MinestormServer()
        minestorm.bind('server', manager)
        # Register shutdown function
        minestorm.register_shutdown_function( manager.shutdown )
