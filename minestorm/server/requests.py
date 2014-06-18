#!/usr/bin/python3
import logging
import minestorm.server.networking
import minestorm.server

class RequestSorter:
    """
    This class manage the request sorter
    by the status code
    """

    def __init__(self):
        self.processors = {} # Initialize processors
        self.logger = logging.getLogger('minestorm.request')

    def register(self, processor):
        """ Register a new processor """
        # Don't insert duplicates
        if processor.name not in self.processors:
            # Register the processor
            self.processors[processor.name] = processor()
            self.logger.debug('Registered network processor for "{0}"'.format( processor.name ))
        else:
            raise RuntimeError('Processor {0} already registered'.format(processor.name))

    def sort(self, request):
        """ Sort a request and pass it to the right processor """
        # Allow only minestorm.server.networking.Request instance
        if isinstance(request, minestorm.server.networking.Request):
            # If no reply was sent yet
            if not request.replied:
                # status key is needed
                if 'status' in request.data:
                    # Check if the status is valid and a processor exists for it
                    if request.data['status'] in self.processors:
                        # Process the request
                        self.processors[ request.data['status'] ]._process( request )
                    else:
                        request.reply({'status': 'invalid_request', 'reason': 'Invalid status code'})
                else:
                    request.reply({'status': 'invalid_request', 'reason': 'Status code not found'})
        else:
            raise RuntimeError('Passed request isn\'t a real request')

class BaseProcessor:
    """
    Representation of a processor
    """
    name = '__base__'
    require_sid = False

    def __new__(cls, *args, **kwargs):
        # Overwrite the class creator to deny
        # instance creation of the base processor
        if cls.name == '__base__':
            raise RuntimeError('Can\'t create instances of the base processor')
        else:
            return super(BaseProcessor, cls).__new__(cls, *args, **kwargs)

    def _process(self, request):
        """ Procesor entry point """
        sessions = minestorm.server.instance.sessions
        # Check if sid is required but not passed
        if self.require_sid and 'sid' not in request.data:
            request.reply({'status': 'failed', 'reason': 'SID not provided'})
        # Check if the sid is required but invalid (badly formatted or expired or never created)
        elif self.require_sid and not sessions.is_valid( request.data['sid'] ):
            request.reply({'status': 'failed', 'reason': 'Invalid SID'})
        else:
            # If a SID was provided, touch the relative session
            # to avoid expiration of it
            if 'sid' in request.data and sessions.is_valid( request.data['sid'] ):
                sessions.get( request.data['sid'] ).touch()
            self.process(request)

    def process(self, request):
        """ Process the request """
        pass

    def __repr__(self):
        return '<Request processor for \'{0}\'>'.format(self.name)

class PingProcessor(BaseProcessor):
    """
    Ping processor
    
    See definition and documentation at
    https://github.com/pietroalbini/minestorm/wiki/networking#ping
    """
    name = 'ping'

    def process(self, request):
        request.reply({'status': 'pong'})

class StartServerProcessor(BaseProcessor):
    """
    Start server processor
    
    See definition and documentation at
    https://github.com/pietroalbini/minestorm/wiki/Networking#start_server
    """
    name = 'start_server'
    require_sid = True

    def process(self, request):
        try:
            minestorm.server.instance.servers.get( request.data['server'] ).start()
        except NameError:
            request.reply({ 'status': 'failed', 'reason': 'Server {} does not exist'.format(request.data['server']) })
        except RuntimeError as e:
            request.reply({ 'status': 'failed', 'reason': str(e) })
        else:
            request.reply({'status':'ok'})

class StopServerProcessor(BaseProcessor):
    """
    Stop server processor
    
    See definition and documentation at
    https://github.com/pietroalbini/minestorm/wiki/Networking#stop_server
    """
    name = 'stop_server'
    require_sid = True

    def process(self, request):
        try:
            minestorm.server.instance.servers.get( request.data['server'] ).stop()
        except NameError:
            request.reply({ 'status': 'failed', 'reason': 'Server {} does not exist'.format(request.data['server']) })
        except RuntimeError as e:
            request.reply({ 'status': 'failed', 'reason': str(e) })
        else:
            request.reply({'status':'ok'})

class NewSessionProcessor(BaseProcessor):
    """
    New session processor
    
    See definition and documentation at
    https://github.com/pietroalbini/minestorm/wiki/Networking#new_session
    """
    name = 'new_session'

    def process(self, request):
        sid = minestorm.server.instance.sessions.new("minestorm").sid
        request.reply({ 'status': 'session_created', 'sid': sid })

class RemoveSessionProcessor(BaseProcessor):
    """
    Remove session processor
    
    See definition and documentation at
    https://github.com/pietroalbini/minestorm/wiki/Networking#remove_session
    """
    name = 'remove_session'
    require_sid = True

    def process(self, request):
        sessions = minestorm.server.instance.sessions
        sessions.remove( request.data['sid'] ) # Remove the session
        request.reply({ 'status': 'ok' })

class ChangeFocusProcessor(BaseProcessor):
    """
    Change focus processor
    
    See definition and documentation at
    https://github.com/pietroalbini/minestorm/wiki/Networking#change_focus
    """
    name = 'change_focus'
    require_sid = True

    def process(self, request):
        sessions = minestorm.server.instance.sessions
        servers = minestorm.server.instance.servers
        # Check if the session exists
        if request.data['server'] in servers.servers:
            sessions.get(request.data['sid']).change_focus(request.data['server']) # Change the focus
            request.reply({ 'status': 'ok' })
        else:
            request.reply({ 'status': 'failed', 'reason': 'Unknow server: {}'.format(request.data['server']) })

class CommandProcessor(BaseProcessor):
    """
    Command processor
    
    See definition and documentation at
    https://github.com/pietroalbini/minestorm/wiki/Networking#command
    """
    name = 'command'
    require_sid = True

    def process(self, request):
        sessions = minestorm.server.instance.sessions
        servers = minestorm.server.instance.servers
        # If the passed server exists pick it
        if 'server' in request.data and request.data['server'] in servers.servers:
            server = servers.get(request.data['server'])
        # Else, if the session has a focused server pick it
        elif sessions.get(request.data['sid']).focus in servers.servers:
            server = servers.get(sessions.get(request.data['sid']).focus)
        # Else return an error
        else:
            request.reply({ 'status': 'failed', 'reason': 'Please specify a valid server' })
            return
        # Execute the command only if the server is running
        if server.status == server.STATUS_STARTED:
            server.command( request.data['command'] ) # Execute the command
            request.reply({ 'status': 'ok' })
        else:
            request.reply({ 'status': 'failed', 'reason': 'Server {} is not running'.format(server.details['name']) })

class StatusProcessor(BaseProcessor):
    """
    Status processor
    
    See definition and documentation at
    https://github.com/pietroalbini/minestorm/wiki/Networking#status
    """
    name = 'status'
    require_sid = True

    def process(self, request):
        servers = minestorm.server.instance.servers
        request.reply({ 'status': 'status_response', 'servers': servers.status() })

class UpdateProcessor(BaseProcessor):
    """
    Update processor
    
    See definition and documentation at
    https://github.com/pietroalbini/minestorm/wiki/Networking#update
    """
    name = 'update'
    require_sid = True

    def process(self, request):
        sessions = minestorm.server.instance.sessions
        servers = minestorm.server.instance.servers
        # Get new lines
        new_lines = sessions.get(request.data['sid']).new_lines
        sessions.get(request.data['sid']).new_lines = []
        # Get server status
        status = []
        for name, server in servers.status().items():
            this = {}
            this['name'] = name
            this['online'] = server['status'] in ( servers.get(name).STATUS_STARTING, servers.get(name).STATUS_STARTED, servers.get(name).STATUS_STOPPING )
            status.append(this)
        # Get the focus
        focus = sessions.get(request.data['sid']).focus
        # Prepare result
        result = { 'status': 'updates' }
        result['new_lines'] = new_lines
        result['servers'] = status
        result['focus'] = focus
        request.reply(result)
