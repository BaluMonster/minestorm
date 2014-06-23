#!/usr/bin/python3
import unittest
import minestorm.common.resources

class TestResource:
    """
    Simple resource used only for testing purposes
    """

    def __init__(self, name='__base__'):
        self.name = name

class Empty:
    """
    Empty class used only for testing purposes
    """
    pass

class ResourcesTestCase( unittest.TestCase ):
    """
    This class will test all the functionalities of the configuration manager
    """

    def setUp(self):
        self.resources = minestorm.common.resources.ResourcesManager()

    def test_resources_creation(self):
        """ Test the creation of resources """
        # Try to create a normal resource
        self.resources.add('test1', subclass_of=TestResource, name_attribute='name', validator=( lambda resource: resource.name != '__base__' ))
        self.assertTrue( self.resources.exists('test1') )
        # Try to provide an invalid subclass_of
        with self.assertRaises( ValueError ):
            self.resources.add('test2', subclass_of="not me")
        # Try to provide an invalid validator
        with self.assertRaises( ValueError ):
            self.resources.add('test3', validator="not me")
        # Try to re-add a resource
        with self.assertRaises( NameError ):
            self.resources.add('test1')

    def test_resource_removing(self):
        """ Test the removing of resources """
        # Create a resource
        self.resources.add('test1', subclass_of=TestResource)
        # Try to remove an existing resource
        self.resources.remove('test1')
        self.assertFalse( self.resources.exists('test1') )
        # Try to remove a non-existing resource
        with self.assertRaises( KeyError ):
            self.resources.remove('test2')

    def test_resource_exists(self):
        """ Test the exists method """
        # Create a resource
        self.resources.add('test1', subclass_of=TestResource)
        # Test the method
        self.assertTrue( self.resources.exists('test1') )
        self.assertFalse( self.resources.exists('test2') )

    def test_resource_get(self):
        """ Test the get method """
        # Create a resource
        self.resources.add('test1', subclass_of=TestResource)
        # Try to get it
        self.assertEqual( self.resources.get('test1').name, 'test1' )
        # Try to get a non-existing resource
        with self.assertRaises( KeyError ):
            self.resources.get('test2')

class ResourceTestCase( unittest.TestCase ):
    """
    This class will test functionalities of the minestorm.common.resources.Resource class
    """

    def setUp(self):
        # Create a new manager and a new resource
        self.resources = minestorm.common.resources.ResourcesManager()
        self.resources.add('test1', subclass_of=TestResource)
        # Create a shortcut for the resource
        self.resource = self.resources.get('test1')

    def test_register_method(self):
        """ Test the register method """
        # Test registering a valid resource
        self.resource.register( TestResource("test1") )
        self.assertTrue( self.resource.has("test1") )
        # Test re-registering a valid resource without force
        with self.assertRaises( NameError ):
            self.resource.register( TestResource("test1") )
        # Test re-registering a valid resource with force
        self.resource.register( TestResource("test1"), force=True )
        self.assertTrue( self.resource.has("test1") )
        # Test registering a resource with the wrong class
        res = Empty()
        res.name = "test2"
        with self.assertRaises( RuntimeError ):
            self.resource.register( res )

    def test_unregister_method(self):
        """ Test the unregister method """
        # Register some resources
        self.resource.register( TestResource("test1") )
        self.resource.register( TestResource("test2") )
        self.resource.register( TestResource("test3") )
        # Try to unregister a resource
        self.resource.unregister("test1")
        self.assertFalse( self.resource.has("test1") )
        # Try to unregister two or more resources
        self.resource.unregister("test2", "test3")
        self.assertFalse( self.resource.has("test2") )
        self.assertFalse( self.resource.has("test3") )
        # Try to unregister a non-existing resource
        with self.assertRaises( KeyError ):
            self.resource.unregister("test4")

    def test_flush_method(self):
        """ Test the flush method """
        # Register some resources
        self.resource.register( TestResource("test1") )
        self.resource.register( TestResource("test2") )
        self.resource.register( TestResource("test3") )
        # Try to flush
        self.resource.flush()
        self.assertFalse( self.resource.has("test1") )
        self.assertFalse( self.resource.has("test2") )
        self.assertFalse( self.resource.has("test3") )

    def test_has_method(self):
        """ Test the has method """
        # Register a resource
        self.resource.register( TestResource("test1") )
        # Try the method
        self.assertTrue( self.resource.has("test1") )
        self.assertFalse( self.resource.has("test2") )

    def test_get_method(self):
        """ Test the get method """
        # Register a resource
        self.resource.register( TestResource("test1") )
        # Try to get an existing resource
        self.assertEqual( self.resource.get("test1").name, "test1" )
        # Try to get a non-existing resource
        with self.assertRaises( KeyError ):
            self.resource.get("test2")
