#!/usr/bin/python3
import curses
from . import components

class Console:
    """
    Manager of the console
    """

    def __init__(self):
        self._initialize_screen()
        self._initialize_curses()
        self._initialize_colours()
        # Some variables
        self.keylisteners = []
        self.stop = False
        # Initialize components
        self.stream = components.StreamComponent(self)
        self.header = components.HeaderComponent(self)
        self.sidebar = components.SidebarComponent(self)
        self.sidebar.update()
        self.infobar = components.InfoBarComponent(self)
        self.inputbar = components.InputBarComponent(self)

    def _initialize_curses(self):
        """ Set some default curses properties """
        curses.nocbreak()
        curses.noecho()
        curses.curs_set(False)
        curses.start_color()
        curses.halfdelay(5)
        # Some shortcuts
        self.lines = curses.LINES
        self.cols = curses.COLS

    def _initialize_colours(self):
        """ Initialize colours """
        self.colours = {}
        # Create a dict which contains all colors which will be registered
        pairs = {
                 "black": [curses.COLOR_BLACK, curses.COLOR_WHITE],
                 "white": [curses.COLOR_WHITE, curses.COLOR_BLACK],
                 "blue": [curses.COLOR_BLUE, curses.COLOR_BLACK],
                 "green": [curses.COLOR_GREEN, curses.COLOR_BLACK],
                 "yellow": [curses.COLOR_YELLOW, curses.COLOR_BLACK],
                 "red": [curses.COLOR_RED, curses.COLOR_BLACK],
        }
        # Register all colors
        i = 1
        for name, definition in pairs.items():
            curses.init_pair(i, definition[0], definition[1]) # Initialize the color pair
            self.colours[name] = curses.color_pair(i) # Register the color pair
            i += 1

    def _initialize_screen(self):
        """ Initialize the screen """
        self.screen = curses.initscr()
        self.screen.keypad(1) # Allow curses to interpretate escape characters

    def register_key_listener(self, listener, type="all"):
        """ Register a key listener - type can be 'all', 'chars', and 'special' """
        if type in ('all', 'chars', 'special'):
            self.keylisteners.append({'listener': listener, 'type': type})
        else:
            raise RuntimeError('type must be "all", "chars" or "special"')

    def emit_key(self, key):
        """ Emit a key pressed event """
        # Discover key type
        if key <= 255:
            key_type = "chars"
        else:
            key_type = "special"
        # Emit the event
        for listener in self.keylisteners:
            # Call the listener only if the type is correct
            if listener['type'] == 'all' or listener['type'] == key_type:
                listener['listener'](key) # Call the listener

    def load_updates(self, data):
        """ Load updates from the requests """
        # Accept only "updates" status codes
        if data['status'] == 'updates':
            # Load new lines
            for line in data['new_lines']:
                self.stream.add_line(line)
            # Load servers
            self.sidebar.flush_servers()
            for server in data['servers']:
                self.sidebar.add_server(server['name'], server['online'])
            # Set focused server
            if data['focus']:
                self.sidebar.set_current_server(data['focus'])
            self.sidebar.set_box_value('RAM', data['ram_used'])

    def loop(self):
        """ Main loop """
        try:
            while self.stop == False:
                # Get a key and emit the event
                key = self.screen.getch()
                if key != -1:
                    self.emit_key(key)
        except KeyboardInterrupt:
            pass
        finally:
            curses.endwin()
