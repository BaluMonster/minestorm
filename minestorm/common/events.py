#!/usr/bin/python3
import logging
import minestorm

class EventsManager:
    """
    Class which manages all events in minestorm
    """

    def __init__(self):
        self._events = {}

    def create(self, name):
        """ Create a new event """
        # Prevent creation of two equal events
        if name in self._events:
            raise NameError('There is another event called {}'.format(name))
        # Create the event
        self._events[name] = Event(name)

    def listen(self, event, subscriber, priority=0):
        """ Listen to a specific event """
        try:
            event = self._events[event]
        except KeyError:
            raise ValueError('There is no event with the {} name'.format(event))
        # Listen to that event
        event.listen(subscriber, priority)

    def unlisten(self, event, subscriber, priority=0):
        """ Remove listening from an event """
        try:
            event = self._events[event]
        except KeyError:
            raise ValueError('There is no event with the {} name'.format(event))
        # Unlisten from that event
        event.unlisten(subscriber, priority)

    def trigger(self, event, data={}):
        """ Trigger an event """
        try:
            event = self._events[event]
        except KeyError:
            raise ValueError('There is no event with the {} name'.format(event))
        # Trigger that event
        return event.trigger(data)

    def get(self, event):
        """ Get an event object """
        return self._events[event]

    def exists(self, event):
        """ Check if an event exists """
        return event in self._events

class Event:
    """
    Representation of an event
    """

    def __init__(self, name):
        self.name = name
        self._listeners = {}
        self._priority_range = 0, 100 # Range for priority

    def listen(self, subscriber, priority):
        """ Listen to this event """
        # Add the priority if it doesn't exists
        if priority not in self._listeners:
            self._listeners[priority] = set() # Create the priority container if it don't exists
        # Prevent adding of non-callable objects
        if not callable(subscriber):
            raise ValueError('Object {!r} is not callable'.format(subscriber))
        # Prevent adding out of range priorities
        if priority < self._priority_range[0] or priority > self._priority_range[1]:
            raise ValueError('Priority {0} out of range ({1[0]}-{1[1]})'.format(priority, self._priority_range))
        # Prevent adding the same subscriber with same priority two or more times
        if subscriber in self._listeners[priority]:
            raise ValueError('Can\'t add the same subscriber with the same priority two times')
        # Add it (finally!)
        self._listeners[priority].add(subscriber)

    def unlisten(self, subscriber, priority):
        """ Remove listening from the event """
        try:
            self._listeners[priority].remove(subscriber) # Remove from the set
        except KeyError:
            raise ValueError('The object {!r} isn\'t listening the event {} with priority {}'.format(subscriber, self.name, priority))

    def trigger(self, data):
        """ Trigger this event """
        process = TriggeredEvents(self, data)
        process.trigger()
        return process

    def _listeners_list(self):
        """ Return an ordered list of all listeners """
        result = []
        # Sort listeners by priority (100 -> 0)
        sort = sorted(self._listeners.items(), key=lambda item: item[0], reverse=True)
        for priority, listeners in sort:
            # Add each listener to the result
            result += list(listeners)
        return result

class TriggeredEvents:
    """
    Representation of a triggered event
    It actually trigger the event, calling subscribers
    and collecting output
    """

    def __init__(self, event, data):
        self._event = event
        self._trigger_start = False
        self._trigger_completed = False
        self._block = False
        self._retrigger = False
        self.blocked = False
        self.retriggered = False
        self.data = data
        self.returns = []

    def trigger(self):
        """ Trigger the event """
        # Prevent triggering multiple times the event
        if self._trigger_start:
            raise RuntimeError('Cannot trigger a triggered event')
        self._trigger_start = True
        # Call all listeners
        listeners = self._event._listeners_list()
        # While used for retrigger
        while True:
            for listener in listeners:
                # Break the cycle if the trigger is blocked
                if self._block:
                    break
                # Call the listener
                result = listener(self)
                # If the listener returned something, append it to the returns list
                if result != None:
                    self.returns.append(result)
            # Exit if retrigger wasn't called
            if not self._retrigger:
                break
            self._retrigger = False # Prevent infinite loops
            self._block = False # Prevent event blocking after retrigger
        # Mark the trigger as complete
        self._trigger_completed = True

    def block(self):
        """ Block the trigger process """
        # Prevent blocking triggered events (it's useless)
        if self._trigger_completed:
            raise RuntimeError('Cannot block a completly triggered event')
        # Block the event
        self._block = True
        self.blocked = True

    def retrigger(self):
        """ Re-trigger the event """
        # Block the propagation of the current trigger process
        try:
            self.block()
        except RuntimeError:
            self._trigger_completed = False
        else:
            self.blocked = False # Don't mark as blocked
        # Re-trigger the event
        self._retrigger = True
        self.retriggered = True
