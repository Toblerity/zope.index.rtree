# index for catalog    
import baseIndex

import zope.interface
import zope.catalog.attribute
import zope.catalog.interfaces
import zope.container.contained

class ISpatialIndex(zope.catalog.interfaces.IAttributeIndex,
                  zope.catalog.interfaces.ICatalogIndex):
    """Interface-based catalog spatial index
    """

class SpatialIndex(zope.catalog.attribute.AttributeIndex,
                   baseIndex.SpatialIndex,
                   zope.container.contained.Contained):

    zope.interface.implements(ISpatialIndex)
