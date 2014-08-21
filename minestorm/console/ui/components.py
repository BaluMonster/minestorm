#!/usr/bin/python3
import curses
import time
import threading
import minestorm

class BaseComponent:
    """
    Abstraction of a component
    """

    height = 1
    width = 1
    start_y = 0
    start_x = 0
    background = 'white'

    def __init__(self, screen):
        self.screen = screen
        self.colours = screen.colours
        self.component = screen.screen.subwin( self.height, self.width, self.start_y, self.start_x ) # Create the component
        self.component.bkgd(' ', self.colours[self.background])
        # Automatically register the keys listener
        if hasattr(self, 'listen_keys'):
            screen.register_key_listener(self.listen_keys)

    def refresh(self):
        """ Refresh the component """
        self.component.refresh()

    def erase(self, *lines):
        """ Erase the input box """
        # If the number of lines is 0
        # erase all of them
        if len(lines) == 0:
            lines = range(0, self.height-1)
        # Erase passed lines
        for line in lines:
            self.component.addstr(line, 0, ' '*(self.width-1), self.colours[self.background])

class HeaderComponent(BaseComponent):
    """
    The header
    """

    height = 1
    width = None # Set it later
    background = 'black'

    def __init__(self, screen):
        self.width = screen.cols
        super(HeaderComponent, self).__init__(screen)

    def left_message(self, message):
        """ Set the left header message """
        self.component.addstr(0, 0, message, self.colours['black'])
        self.refresh()

    def right_message(self, message):
        """ Set the right header message """
        self.component.addstr(0, self.width-len(message)-1, message, self.colours['black'])
        self.refresh()

class StreamComponent(BaseComponent):
    """
    The stream
    """

    height = None # Set it later
    width = None # Set it later
    start_y = 1
    start_x = 0

    def __init__(self, screen):
        self.height = screen.lines - 3
        self.width = screen.cols - 30
        super(StreamComponent, self).__init__(screen)
        # Setup lines
        self.lines = []
        self.position = 0

    def add_line(self, line):
        """ Add a line to the stream """
        self.lines.append(line) # Append the line to the stream
        # Move the position to the last line
        # if the position wasn't moved
        self.position = len(self.lines)
        self.update() # Update the screen

    def update(self):
        """ Update the screen """
        max_lines = self.height
        # If the number of lines is lower than the max number of lines
        # display all of them
        # Else display only the desidered chunk
        if ( len(self.lines) < max_lines ) or self.position-max_lines < 0:
            chunk = self.lines
        else:
            chunk = self.lines[ (self.position-max_lines) : self.position ]
        # Split lines into small parts
        # Needed to avoid lines truncating
        new_chunk = []
        for line in chunk:
            # If the length of the line is greater than the screen size
            # split the line
            if len(line) > (self.width - 1):
                position = 0
                while 1:
                    position_max = position + self.width - 1
                    # If the expected part of the line is lower than the
                    # total line length add the remaining part and break
                    # the loop
                    if position_max > len(line):
                        new_chunk.append( line[ position: ] )
                        break
                    # Else add the expected part
                    else:
                        new_chunk.append( line[ position:position_max ] )
                        position += self.width - 1
            # If the line length is lower than the stream width
            # simply add it
            else:
                new_chunk.append( line )
        # Now get only the last part of the chunk
        chunk = new_chunk[ :max_lines ]
        # Display the chunk
        i = 0
        for line in chunk:
            self.erase(i)
            self.component.addstr(i, 0, line, self.colours['white']) # Add the line
            i += 1
        self.refresh() # Refresh the screen

    def listen_keys(self, key):
        """ Listen for keys """
        # Up arrow key
        if key == curses.KEY_UP:
            # The position must be greater than the height
            # else the console crashes
            if self.position > self.height:
                self.position -= 1
                self.update()
        # Down arrow key
        elif key == curses.KEY_DOWN:
            # The position must be lower than the number of lines
            # else the console crashes
            if self.position < len(self.lines):
                self.position += 1
                self.update()

class SidebarComponent(BaseComponent):
    """
    The sidebar
    """

    height = None # Set it later
    width = 30
    start_y = 1
    start_x = None # Set it later

    def __init__(self, screen):
        self.height = screen.lines - 3
        self.start_x = screen.cols - 30
        super(SidebarComponent, self).__init__(screen)
        # Setup boxes
        self.boxes = {}
        self.boxes_ordered = []
        self.add_box('RAM', True)

    def add_box(self, name, progress=False, colour='white'):
        """ Add a box to the sidebar """
        box = SidebarBox(name, progress, colour)
        # Register the box both in the standard dict and in the ordered list
        self.boxes[name] = box
        self.boxes_ordered.append(box)
        self.update()

    def remove_box(self, name):
        """ Remove a box """
        box = self.boxes.pop(name) # Pop the box from the dict
        self.boxes_ordered.remove(box) # Remove the box also from the ordered list
        self.update()

    def set_box_value(self, box, value):
        """ Set the value of a box """
        # If the box is a progress bar
        if self.boxes[box].progress:
            value = int(value)
            # If the value is greater than 100 edit it and set 100
            if value > 100:
                value = 100
        self.boxes[box].value = value
        self.update()

    def set_box_colour(self, box, colour):
        """ Set the colour of a box """
        self.boxes[box].colour = colour
        self.update()

    def update(self):
        """ Update the sidebar """
        self.erase()
        self._update_boxes()
        self._update_server_list()
        self.refresh()

    def _update_boxes(self):
        """ Update boxes """
        line = 1
        for box in self.boxes_ordered:
            box.render(line, self) # Render the box
            line += 3

    def _update_server_list(self):
        """ Update the server list """
        servers_list = minestorm.get('console.servers').all()
        if len(servers_list) > 0:
            top = self.height-len(servers_list)-2 # Calculate the top line
        else:
            top = self.height-3
        self.component.addstr(top, 3, 'Available servers:', curses.A_BOLD)
        # Get servers list
        servers = list(servers_list.keys())
        servers.sort()
        servers.sort(key=lambda s: servers_list[s].status in ('STARTING', 'STARTED', 'STOPPING'), reverse=True)
        # Render each server
        if len(servers_list) > 0:
            i = 1
            for server in servers:
                self._render_server(top+i, server )
                i += 1
        else:
            self.component.addstr(top+1, 3, "No server available")

    def _render_server(self, line, name):
        """ Render a single server """
        server = minestorm.get('console.servers').get(name)
        # Get the bullet colour
        if server.status in ('STARTING', 'STARTED', 'STOPPING'):
            bullet_colour = self.colours['green'] | curses.A_BOLD
        else:
            bullet_colour = self.colours['red'] | curses.A_BOLD
        # Render!
        if minestorm.get('console.ui').focus == name:
            self.component.addstr(line, 1, '>', self.colours['blue'] | curses.A_BOLD)
        self.component.addstr(line, 3, name)
        self.component.addstr(line, self.width-2, '⚫', bullet_colour)

class SidebarBox:
    """
    A box of the sidebar
    """

    def __init__(self, name, progress=False, colour='white'):
        self.name = name
        self.progress = progress
        self.value = 0 if progress else "" # Setup the default value
        self.colour = colour

    def render(self, line, sidebar):
        """ Render the box at the specified line """
        win = sidebar.component
        win.addstr(line, 1, self.name+':')
        # Choose if render the progress-bar or the simple value
        if self.progress:
            # Write the percent value
            percent = str(self.value)+'%' # Prepare the percent value
            win.addstr(line, sidebar.width-len(percent)-1, percent, curses.A_BOLD)
            # Write the progress bar
            win.addstr(line+1, 1, '[')
            win.addstr(line+1, 2, '='*int(self.value*(sidebar.width-3)/100), sidebar.colours[self._get_progress_bar_colour()])
            win.addstr(line+1, sidebar.width-2, ']')
        else:
            win.addstr(line+1, 1, self.value, sidebar.colours[self.colour] | curses.A_BOLD)

    def _get_progress_bar_colour(self):
        """ Get the progress bar color """
        if self.value < 75:
            colour = 'green'
        elif self.value < 90:
            colour = 'yellow'
        else:
            colour = 'red'
        return colour

class InfoBarComponent(BaseComponent):
    """
    The info bar
    """

    height = 1
    width = None # Set it later
    start_y = None # Set it later
    start_x = 0
    background = 'black'

    def __init__(self, screen):
        self.width = screen.cols
        self.start_y = screen.lines - 2
        self.clearer_thread = None
        super(InfoBarComponent, self).__init__(screen)

    def message(self, message, clear=True, clear_after=3):
        """ Set the message """
        self.erase(0)
        self.component.addstr(0, 0, message, self.colours['black'])
        self.refresh()
        # Start the clearer thread if clear is True
        if clear:
            at = time.time()+clear_after
            # If the thread is already running update the stop_at time
            # Else start a new thread
            if self.clearer_thread != None:
                self.clearer_thread.stop_at = at
            else:
                self.clearer_thread = InfobarClearerThread(at)
                self.clearer_thread.start()

    def clear(self):
        """ Clear the message """
        self.message("")
        # Reset the clearer_thread
        self.clearer_thread = None

class InputBarComponent(BaseComponent):
    """
    The command bar
    """

    height = 1
    width = None # Set it later
    start_y = None # Set it later
    start_x = 0

    def __init__(self, screen):
        self.width = screen.cols
        self.start_y = screen.lines - 1
        super(InputBarComponent, self).__init__(screen)
        self.screen.screen.move(self.start_y, 0)
        self.content = ""
        self.cursor_position = 0

    def listen_keys(self, key):
        """ Listen for keys """
        if key == curses.KEY_BACKSPACE:
            # Don't remove the last character if the content is empty
            if self.content != "":
                before_part = self.content[:(self.cursor_position-1)]
                after_part = self.content[self.cursor_position:]
                self.content = before_part + after_part
                self.cursor_position -= 1
                self.erase(0)
        elif key == 10: # Enter key
            if self.content != "":
                # It the command starts with "!", it's a console command
                if self.content[0] == "!":
                    # Execute the command
                    result = minestorm.get("console.commands").route( self.content )
                    if result:
                        # If the command returned a result, display it
                        minestorm.get("console.ui").infobar.message(result)
                else:
                    # Send command to the backend
                    sid = minestorm.get("console.networking").sid
                    try:
                        response = minestorm.get("console.networking").request({ 'status': 'command', 'command': self.content, 'sid': sid })
                    except Exception as e:
                        # If an exception occured display it in the infobar
                        minestorm.get("console.ui").infobar.message("Exception: {!s}".format(e))
                    # If the request failed and a reason is returned display it
                    if response['status'] == 'failed' and 'reason' in response:
                        minestorm.get("console.ui").infobar.message(response['reason'])
            self.content = ""
            self.cursor_position = 0
            self.erase(0)
        # Move the cursor back
        elif key == curses.KEY_LEFT:
            if self.cursor_position > 0:
                self.cursor_position -= 1
        # Move the cursor forward
        elif key == curses.KEY_RIGHT:
            if self.cursor_position < len(self.content):
                self.cursor_position += 1
        elif key <= 255:
            before_part = self.content[:self.cursor_position]
            after_part = self.content[self.cursor_position:]
            self.content = before_part+chr(key)+after_part
            self.cursor_position += 1 # Move the cursor
        self.screen.screen.addstr(self.start_y, 0, self.content, self.colours['white'])
        self.screen.screen.move(self.start_y, self.cursor_position)
        self.refresh()

class InfobarClearerThread( threading.Thread ):
    """
    Thread which is started by InfoBarComponent
    when a new message is inserted
    """

    def __init__(self, at):
        self.stop_at = at
        super(InfobarClearerThread, self).__init__()

    def run(self):
        # Execute it until self.stop_at is equals or greater than time.time()
        while self.stop_at > time.time():
            time.sleep(0.5)
        minestorm.get('console.ui').infobar.clear()
