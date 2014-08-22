#!/usr/bin/python3
import unittest
import minestorm.common.events

class EventsTestCase( unittest.TestCase ):
    """
    This class will test all the functionalities of the events system
    """

    def setUp(self):
        self.events = minestorm.common.events.EventsManager()

    def test_create_events(self):
        """ Test if an event is created successifully """
        # First check standard event creation
        self.events.create('test')
        self.assertTrue( self.events.exists('test') )
        # Next check creating an event which already exists
        with self.assertRaises( NameError ):
            self.events.create('test')

    def test_listen_event(self):
        """ Test if it's possible to listen to events """
        # Setup things
        subscriber = lambda e: None # Sample subscriber
        self.events.create('test') # Register a sample event
        event = self.events.get('test') # Get the event
        # Try to listen correctly
        self.events.listen('test', subscriber, 10)
        self.assertTrue( subscriber in event._subscribers[10] )
        self.events.unlisten('test', subscriber, 10) # Unlisten afterr to prevents errors in the future
        # Try to pass an invalid event name
        with self.assertRaises( ValueError ):
            self.events.listen('not_exists', subscriber, 10)
        # Try to pass an uncallable object
        with self.assertRaises( ValueError ):
            self.events.listen('test', "I'm not callable", 10)
        # Try to pass an out of range priority (lower)
        with self.assertRaises( ValueError ):
            self.events.listen('test', subscriber, event._priority_range[0]-1)
        # Try to pass an out of range priority (higher)
        with self.assertRaises( ValueError ):
            self.events.listen('test', subscriber, event._priority_range[1]+1)

    def test_unlisten_event(self):
        """ Test if it's possible to unlisten from an event """
        # Setup things
        subscriber = lambda e: None
        self.events.create('test')
        event = self.events.get('test')
        # First try to unlisten it properly
        self.events.listen('test', subscriber, 20)
        self.assertTrue( subscriber in event._subscribers[20] )
        self.events.unlisten('test', subscriber, 20)
        self.assertFalse( subscriber in event._subscribers[20] )
        # Next try to unlisten a subscriber which wasn't listening
        with self.assertRaises( ValueError ):
            self.events.unlisten('test', subscriber, 10)
        # Also try to unlisten from an event which doesn't exist
        with self.assertRaises( ValueError ):
            self.events.unlisten('test2', subscriber, 20)
