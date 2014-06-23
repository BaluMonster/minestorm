#!/usr/bin/python3
import unittest
import minestorm.test.container
import minestorm.test.common.configuration
import minestorm.test.common.resources

def load(case):
    """ Add a test to the suite """
    tests = unittest.makeSuite(case)
    return tests

def generate_suite():
    """ Generate the suite """
    suite = unittest.TestSuite()
    suite.addTest( load( minestorm.test.container.ContainerTestCase ) )
    suite.addTest( load( minestorm.test.common.configuration.ConfigurationTestCase ) )
    suite.addTest( load( minestorm.test.common.resources.ResourcesTestCase ) )
    suite.addTest( load( minestorm.test.common.resources.ResourceTestCase ) )
    return suite

def run():
    """ Run the unittest """
    suite = generate_suite()
    runner = unittest.TextTestRunner()
    runner.run( suite )
