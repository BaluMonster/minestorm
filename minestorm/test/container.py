#!/usr/bin/python3
import unittest
import minestorm

class ContainerTestCase( unittest.TestCase ):
    """
    This class will test all the functionalities of the container
    """

    def setUp(self):
        self.container = minestorm.Container()

    def tearDown(self):
        self.container.flush() # Flush the container
        del self.container

    def test_binding_items(self):
        """ Test the bind method """
        # Try to bind something in it
        self.container.bind('test1', 'hello')
        self.assertEqual( self.container.get('test1'), 'hello' )
        # Try to bind something already in the container
        with self.assertRaises( KeyError ):
            self.container.bind('test1', 'bye')
        # Try to force bind something already in the container
        self.container.bind('test1', 'bye', force=True)
        self.assertEqual( self.container.get('test1', 'bye'), 'bye' )

    def test_getting_items(self):
        """ Test the get method """
        # Add some stuff
        self.container.bind('test1', 'hello')
        # Test getting existing item
        self.assertEqual( self.container.get('test1'), 'hello' )
        # Test getting not existing item
        with self.assertRaises( KeyError ):
            self.container.get('test2')
        # Test getting items with a default
        self.assertEqual( self.container.get('test1', default='default'), 'hello' )
        self.assertEqual( self.container.get('test2', default='default'), 'default' )

    def test_removing_items(self):
        """ Test remove method """
        # Add some stuff
        self.container.bind('test1', 'hello')
        # Try to remove an existing item
        self.container.remove('test1')
        self.assertFalse( self.container.has('test1') )
        # Try to remove a non-existing item
        with self.assertRaises( KeyError ):
            self.container.remove('test2')

    def test_has_items(self):
        """ Test has method """
        # Add some stuff
        self.container.bind('test1', 'hello')
        # Try to use has
        self.assertTrue( self.container.has('test1') )
        self.assertFalse( self.container.has('test2') )

    def test_flush_items(self):
        """ Test flush method """
        # Add some stuff
        self.container.bind('test1', 'hello')
        self.container.bind('test2', 'hello')
        # Check flush remove all items
        self.container.flush()
        self.assertFalse( self.container.has('test1') )
        self.assertFalse( self.container.has('test2') )
