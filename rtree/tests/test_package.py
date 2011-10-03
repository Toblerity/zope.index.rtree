# -*- coding: utf-8 -*-

import unittest
import pkg_resources
from zope.index.SpatialIndex import  tests
#from zope.testing import doctest
import doctest


def make_test(dottedname):
    test = doctest.DocTestSuite(
        dottedname, setUp=tests.siteSetUp, tearDown=tests.siteTearDown,
        optionflags=doctest.ELLIPSIS + doctest.NORMALIZE_WHITESPACE)
    test.layer = tests.SpatialIndexCoreIndexSpatialLayer(tests)
    return test


def suiteFromPackage(name):
    files = pkg_resources.resource_listdir(__name__, name)
    suite = unittest.TestSuite()
    for filename in files:
        if not filename.endswith('.py'):
            continue
        if filename.endswith('_fixture.py'):
            continue
        if filename == '__init__.py':
            continue

        dottedname = 'zope.index.SpatialIndex.tests.%s.%s' % (name, filename[:-3])
        suite.addTest(make_test(dottedname))
    return suite


def test_suite():
    suite = unittest.TestSuite()
    readme = doctest.DocFileSuite(
        '../README.txt', globs={'__name__': 'zope.index.SpatialIndex'},
        optionflags=(doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS))
    readme.layer = tests.SpatialIndexCoreIndexSpatialLayer(tests)
    suite.addTest(readme)
    for name in ['storage', 'index']:
        suite.addTest(suiteFromPackage(name))
    return suite
