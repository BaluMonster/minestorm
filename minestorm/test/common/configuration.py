#!/usr/bin/python3
import unittest
import tempfile
import minestorm.common.configuration

class ConfigurationTestCase( unittest.TestCase ):
    """
    This class will test all the functionalities of the configuration manager
    """

    def setUp(self):
        self.configuration = minestorm.common.configuration.ConfigurationManager()

    def test_load_one_file(self):
        """ Test loading of one file into the configuration """
        # Add some default values to the configuration to check later
        # if them will be flushed
        self.configuration.update('to_be_flushed', 'yes')
        # Create one temporary file to load
        with tempfile.NamedTemporaryFile(mode='w+') as f:
            # Write something in it
            f.write('{"test1":{"test2":"a","test3":{"test4":"b","test5":"c"}}}')
            f.flush()
            # Load the file in the configuration
            self.configuration.load( f.name )
        # Now check if values are inserted correctly
        self.assertEqual( self.configuration.get('test1.test2'), 'a' )
        self.assertEqual( self.configuration.get('test1.test3.test4'), 'b' )
        self.assertEqual( self.configuration.get('test1.test3.test5'), 'c' )
        # Check if flush was executed
        self.assertFalse( self.configuration.has('to_be_flushed') )

    def test_flush_not_executed_during_load_if_specified(self):
        """ Test that flush will not be executed if the flush parameter is set to false in load """
        # Add some default values to the configuration to check later
        # if them will be flushed
        self.configuration.update('to_be_flushed', 'yes')
        # Create one temporary file to load
        with tempfile.NamedTemporaryFile(mode='w+') as f:
            # Write something in it
            f.write('{"test1":"a"}')
            f.flush()
            # Load the file in the configuration
            self.configuration.load( f.name, flush=False )
        # Check if flush was not executed
        self.assertTrue( self.configuration.has('to_be_flushed') )

    def test_load_multiple_files(self):
        """ Test loading of multiple files """
        # Create one temporary file to load
        with tempfile.NamedTemporaryFile(mode='w+') as f:
            # Write something in it
            f.write('{"test1":"a","test2":{"test3":"b"}}')
            f.flush()
            # Create another temporary file to load
            with tempfile.NamedTemporaryFile(mode='w+') as f2:
                # Write something in it
                f2.write('{"test1":{"test4":"c","test5":"d"},"test2":"e"}')
                f2.flush()
                # Load the file in the configuration
                self.configuration.load( f.name, f2.name )
        # Now check if all things were added
        self.assertEqual( self.configuration.get('test1'), 'a' )
        self.assertEqual( self.configuration.get('test1.test4'), 'c' )
        self.assertEqual( self.configuration.get('test1.test5'), 'd' )
        self.assertEqual( self.configuration.get('test2'), 'e' )
        self.assertEqual( self.configuration.get('test2.test3'), 'b' )

    def test_getting_entries(self):
        """ Test the get method """
        # Add some stuff
        self.configuration.update('test1', 'a')
        # Check on existing entry
        self.assertEqual( self.configuration.get('test1'), 'a' )
        # Check on non-existing entry
        with self.assertRaises( KeyError ):
            self.configuration.get('test2')
        # Check with defaults
        self.assertEqual( self.configuration.get('test1', default='default'), 'a' )
        self.assertEqual( self.configuration.get('test2', default='default'), 'default' )

    def test_updating_entries(self):
        """ Test the update method """
        # Add an entry which is not in the configuration
        self.configuration.update('test1', 'a')
        self.assertEqual( self.configuration.get('test1'), 'a' )
        # Update an existing entry
        self.configuration.update('test1', 'b')
        self.assertEqual( self.configuration.get('test1'), 'b' )

    def test_has_entries(self):
        """ Test the has method """
        # Add some stuff
        self.configuration.update('test1', 'a')
        # Test it!
        self.assertTrue( self.configuration.has('test1') )
        self.assertFalse( self.configuration.has('test2') )

    def test_removing_entries(self):
        """ Test the remove method """
        # Add some stuff
        self.configuration.update('test1', 'a')
        # Try to remove an existing item
        self.configuration.remove('test1')
        self.assertFalse( self.configuration.has('test1') )
        # Try to remove a non-existing item
        with self.assertRaises( KeyError ):
            self.configuration.remove('test2')

    def test_flush_entries(self):
        """ Test the flush method """
        # Add some stuff
        self.configuration.update('test1', 'a')
        self.configuration.update('test2', 'b')
        # Flush the configuration and test it
        self.configuration.flush()
        self.assertFalse( self.configuration.has('test1') )
        self.assertFalse( self.configuration.has('test2') )
