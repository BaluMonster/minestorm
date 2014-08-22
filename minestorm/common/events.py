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
        event.trigger(data)

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
        self._subscribers = {}
        self._priority_range = 0, 100 # Range for priority

    def listen(self, subscriber, priority):
        """ Listen to this event """
        # Add the priority if it doesn't exists
        if priority not in self._subscribers:
            self._subscribers[priority] = set() # Create the priority container if it don't exists
        # Prevent adding of non-callable objects
        if not callable(subscriber):
            raise ValueError('Object {!r} is not callable'.format(subscriber))
        # Prevent adding out of range priorities
        if priority < self._priority_range[0] or priority > self._priority_range[1]:
            raise ValueError('Priority {0} out of range ({1[0]}-{1[1]})'.format(priority, self._priority_range))
        # Prevent adding the same subscriber with same priority two or more times
        if subscriber in self._subscribers[priority]:
            raise ValueError('Can\'t add the same subscriber with the same priority two times')
        # Add it (finally!)
        self._subscribers[priority].add(subscriber)

    def unlisten(self, subscriber, priority):
        """ Remove listening from the event """
        try:
            self._subscribers[priority].remove(subscriber) # Remove from the set
        except KeyError:
            raise ValueError('The object {!r} isn\'t listening the event {} with priority {}'.format(subscriber, self.name, priority))

    def trigger(self, data):
        """ Trigger this event """
        # TODO
        pass

class TriggeredEvents:
    # TODO
    pass
