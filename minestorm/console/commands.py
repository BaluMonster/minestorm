#!/usr/bin/python3
import minestorm
import minestorm.common

class Command:
    """
    Representation of a command
    """
    name = '__base__'
    arguments_count = None

    def __init__(self):
        if self.name == '__base__':
            raise RuntimeError('Can\'t create instances of the base command')

    def _execute(self, arguments):
        """ Execute entry point """
        # If an arguments count is provided check for it
        if self.arguments_count != None:
            if len(arguments) != self.arguments_count:
                # Return an error message
                return 'Wrong number of arguments!'
        # Execute the command
        self.execute(arguments)

    def execute(self, arguments):
        """ Execute the command """
        pass

class CommandsManager( minestorm.common.BaseManager ):
    """
    Class which manage all minestorm console commands
    """
    subclass_of = Command
    resource_name = 'command'

    def route(self, command):
        """ Route the command to the correct processor """
        # Command prefix must be !
        if command[0] == "!":
            # If a space is present in the command split them
            # else the name is the command and the arguments is an empty string
            if " " in command:
                name, arguments = command.split(" ", 1) # Split name and arguments
                name = name[1:] # Remove starting !
                arguments = arguments.split(" ")
            else:
                name = command[1:]
                arguments = []
            # If the command is registered
            if name in self:
                result = self[name].execute(arguments) # Execute the command
                return result
            else:
                return 'Command {} not found'.format(name)
        else:
            return 'Invalid commmand'

class SwitchCommand(Command):
    """
    Command which switch the focused server
    
    Example:
    !switch wonderful_server
    """
    name = 'switch'
    arguments_count = 1

    def execute(self, arguments):
        # Try to switch server
        result = minestorm.get('console.networking').request({ 'status': 'change_focus', 'server': arguments[0], 'sid': minestorm.get('console.networking').sid })
        if result['status'] == 'ok':
            return 'Server switched'
        elif result['status'] == 'failed':
            return result['reason']
        else:
            return 'Unknow reply from minestorm'

class StartCommand(Command):
    """
    Command which start a server
    
    Example:
    !start wonderful_server
    """
    name = 'start'
    arguments_cound = 1

    def execute(self, arguments):
        # Try to start the server
        result = minestorm.get('console.networking').request({'status': 'start_server', 'server': arguments[0], 'sid': minestorm.get('console.networking').sid })
        if result['status'] == 'ok':
            return 'Server started'
        elif result['status'] == 'failed':
            return result['reason']
        else:
            return 'Unknow reply from minestorm'

class StopCommand(Command):
    """
    Command which stop a server
    
    Example:
    !stop wonderful_server
    """
    name = 'stop'
    arguments_cound = 1

    def execute(self, arguments):
        # Try to start the server
        result = minestorm.get('console.networking').request({'status': 'stop_server', 'server': arguments[0], 'sid': minestorm.get('console.networking').sid })
        if result['status'] == 'ok':
            return 'Server stopped'
        elif result['status'] == 'failed':
            return result['reason']
        else:
            return 'Unknow reply from minestorm'
