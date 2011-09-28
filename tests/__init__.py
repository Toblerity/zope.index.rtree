#-*- coding: utf-8 -*-

import zope.component
from zope.component.interfaces import IComponentLookup
from zope.component.testlayer import ZCMLFileLayer
from zope.container.interfaces import ISimpleReadContainer
from zope.container.traversal import ContainerTraversable
from zope.interface import Interface
from zope.site.folder import rootFolder
from zope.site.site import LocalSiteManager, SiteManagerAdapter
from zope.traversing.interfaces import ITraversable
from zope.traversing.testing import setUp


def siteSetUp(test):

    zope.component.hooks.setHooks()

    # Set up site manager adapter
    zope.component.provideAdapter(
        SiteManagerAdapter, (Interface,), IComponentLookup)

    # Set up traversal
    setUp()
    zope.component.provideAdapter(
        ContainerTraversable, (ISimpleReadContainer,), ITraversable)

    # Set up site
    site = rootFolder()
    site.setSiteManager(LocalSiteManager(site))
    zope.component.hooks.setSite(site)

    return site


def siteTearDown(test):
    zope.component.hooks.resetHooks()
    zope.component.hooks.setSite()


class SpatialIndexCoreIndexSpatialLayer(ZCMLFileLayer):
    pass
