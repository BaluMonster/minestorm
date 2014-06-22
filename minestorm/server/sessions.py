#!/usr/bin/python3
import logging
import uuid
import time
import threading
import minestorm

class SessionsManager:
    """
    Class which manage all sessions
    """

    def __init__(self):
        self.sessions = {}
        self.logger = logging.getLogger('minestorm.sessions')
        # Initialize the thread
        self.thread = SessionsClearerThread(self)
        self.thread.start()

    def new(self, user):
        """ Create a new session """
        sid = str( uuid.uuid4() ) # Generate an unique id for this session
        # Actually user authentication is not implemented, so
        # user must be minestorm
        if user == "minestorm":
            # Create the session
            session = Session(sid, user)
            self.sessions[sid] = session
            self.logger.info('Created a new session with SID {}'.format(sid))
            return session
        else:
            raise RuntimeError('Invalid credentials')

    def get(self, sid):
        """ Get an existing session """
        return self.sessions[sid]

    def is_valid(self, sid):
        """ Check if a SID is valid """
        # Get the expiration time
        expire_at = time.time() - minestorm.get('configuration').get('sessions.expiration.time')
        # First check if the SID exists
        if sid in self.sessions:
            # Now check if it isn't expired
            if self.sessions[sid].last_packet > expire_at:
                return True
            else:
                return False
        else:
            return False

    def clear(self):
        """ Clear expired sessions """
        # Clean expired sessions
        for session in self.sessions.copy().values():
            # Remove the session if it isn't valid
            if not self.is_valid(session.sid):
                self.remove(session.sid) # Just do it, ok?
        self.logger.debug('Finished sessions clearing')

    def remove(self, sid):
        """ Remove a session by its sid """
        if sid in self.sessions:
            # Delete the session
            del self.sessions[sid]
            self.logger.info('Removed session with SID {}'.format(sid))
        else:
            raise KeyError('Invalid sid: {}'.format(sid))

    def add_line(self, server, line):
        """ Add a line to all sessions which are listening that server """
        for session in self.sessions:
            # Add the line only if the server focus is in that server
            if self.get(session).focus == server:
                self.get(session).add_line(line) # Add the line

class Session:
    """
    Representation of a session
    """

    def __init__(self, sid, user):
        self.sid = sid
        self.user = user
        self.new_lines = []
        self.focus = None
        self.last_packet = time.time()

    def touch(self):
        """ Update the last packet time """
        self.last_packet = time.time()
        logging.getLogger('minestorm.sessions').debug('Touched session {}'.format(self.sid))

    def add_line(self, line):
        """ Add a line to the session stream """
        self.new_lines.append(line)

    def change_focus(self, new):
        """ Change the session focus """
        self.focus = new
        self.new_lines = [] # Clear new lines

class SessionsClearerThread(threading.Thread):
    """
    Thread which will clean all expired sessions
    Expiration time and timer length are set in the configuration
    """

    def __init__(self, manager):
        self.manager = manager
        self.stop = False
        super(SessionsClearerThread, self).__init__()

    def run(self):
        while not self.stop:
            self.manager.clear()
            # Go to the bed!
            time.sleep( minestorm.get('configuration').get('sessions.expiration.check_every') )
