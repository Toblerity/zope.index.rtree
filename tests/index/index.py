"""
Spatial index test
===================

Exercise the spatial index.

Create an in-memory zodb.

  >>> import ZODB.tests.util
  >>> db = ZODB.tests.util.DB()
  >>> dbconn = db.open()
  >>> dbroot = dbconn.root()
  >>> import BTrees

Add the site.

  >>> from zope.component.hooks import getSite
  >>> site = dbroot['site'] = getSite()
  
Setup the index. Note that writethrough is False which means the rtree will be buffering stuff. It's important to test this
situation, because the buffering needs to play nice with transaction abort, rollbacks and so on. There should never be
any stale data due to buffering.
Without buffering and writethrough the performance would be worse and create many possibly unneccessary btree/zodb writes.

  >>> settings = dict( dimension = 2, leaf_capacity = 20, pagesize = 4096, near_minimum_overlap_factor = 20, writethrough = False, buffering_capacity = 100, family = BTrees.family64 )
  >>> site['index'] = index = SpatialIndex( field_name = 'boundingBox', interface = IBounded, field_callable=False, settings = settings )
  >>> transaction.commit()
  
We need to call commit here, otherwise the following transaction.begin() calls abort() and this would cause the index to
be removed from the zodb again. We don't want this to happen.

Let's test simple index_doc and some queries.

  >>> transaction.begin()
  <...>
  >>> index.index_doc( 0, House('Mansion', (5,5,20,10)) )
  >>> index.count( (0,0,100,100) )
  1L
  >>> index.documentCount()
  1
  >>> list( index.intersection( (0,0,100,100) ) )
  [0L]
  >>> list( index.intersection( (100,100,200,200) ) )
  []
  >>> index.index_doc( 1, House('Cottage', (20,20,25,25)) )
  >>> index.count( (0,0,100,100) )
  2L
  >>> index.documentCount()
  2
  >>> sorted( list( index.intersection( (0,0,100,100) ) ) )
  [0L, 1L]

Test unindex_doc:

  >>> index.unindex_doc( 0 )
  >>> index.count( (0,0,100,100) )
  1L
  >>> index.documentCount()
  1
  >>> list( index.intersection( (0,0,100,100) ) )
  [1L]
  >>> index.unindex_doc( 1 )
  >>> index.count( (0,0,100,100) )
  0L
  >>> index.documentCount()
  0
  
Test clear:

  >>> index.index_doc( 0, House('Mansion', (5,5,20,10)) )
  >>> index.count( (0,0,100,100) )
  1L
  >>> index.clear()
  >>> index.count( (0,0,100,100) )
  0L
  >>> index.documentCount()
  0
  >>> transaction.commit()


Let's test savepoints and aborts.

  >>> transaction.begin()
  <...>
  >>> index.documentCount()
  0
  >>> #log( 'PRE-SAVEPOINT' )
  >>> sp = transaction.savepoint()
  >>> #log( 'POST-SAVEPOINT' )
  >>> index.index_doc( 0, House('Mansion', (5,5,20,10)) )
  >>> index.count( (0,0,100,100) )
  1L
  >>> index.documentCount()
  1
  >>> #log( 'PRE-ABORT' )
  >>> transaction.abort()
  >>> #log( 'POST-ABORT' )
  >>> index.count( (0,0,100,100) )
  0L
  >>> index.documentCount()
  0

Let's test more aborts.

  >>> transaction.begin()
  <...>
  >>> index.index_doc( 1, House('Mansion', (5,5,20,10)) )
  >>> index.count( (0,0,100,100) )
  1L
  >>> transaction.abort()
  >>> index.count( (0,0,100,100) )
  0L
  
Test more complex index/unindex/commit/savepoint/rollback/abort stuff.

  >>> house1, house2, house3, house4, house5, house6 = 1, 2, 3, 4, 5, 6
  >>> index.index_doc( house1, House('Mansion', (5,5,20,10)) )
  >>> index.index_doc( house2, House('Cottage', (20,20,25,25)) )
  >>> index.count( (0,0,100,100) )
  2L
  >>> index.documentCount()
  2
  >>> index._clearBuffer(False)
  >>> 
  >>> #log( 'PRE-SAVEPOINT1' )
  >>> sp = transaction.savepoint()
  >>> #log( 'POST-SAVEPOINT1')
  >>> index.unindex_doc( house1 )
  >>> list(index.intersection( (0,0,100,100) )) == [house2]
  True
  >>> index.documentCount()
  1
  >>> index.unindex_doc( house2 )
  >>> index.count( (0,0,100,100) )
  0L
  >>> index.index_doc( house3, House('Cottage #2', (9,9,25,25)) )
  >>> index.count( (0,0,100,100) )
  1L
  >>> #log( 'PRE-SAVEPOINT2' )
  >>> sp2 = transaction.savepoint()
  >>> #log( struct.unpack( 'I', index.pageData[0][8:12] ) )
  >>> #log( 'POST-SAVEPOINT2' )
  >>> index.index_doc( house4, House('Cottage #2a', (11,11,26,26)) )
  >>> index.count( (0,0,100,100) )
  2L
  >>> index.unindex_doc( house4 )
  >>> index.count( (0,0,100,100) )
  1L
  >>> sorted( index.intersection( (0,0,100,100) ) ) == [house3]
  True
  >>> #log( 'PRE-ROLLBACK2' )
  >>> #log( struct.unpack( 'I', index.pageData[0][8:12] ) )
  >>> sp2.rollback()
  >>> #log( struct.unpack( 'I', index.pageData[0][8:12] ) )
  >>> #log( 'POST-ROLLBACK2' )
  >>> #log( index.count( (0,0,100,100) ) )
  >>> #for obj in index.intersection( (0,0,100,100) ):
  >>> #    log( obj.name )
  >>> index.count( (0,0,100,100) )
  1L
  >>> index.index_doc( house5, House('Cottage #77', (10,10,25,25)) )
  >>> #log( 'PRE-ROLLBACK1' )
  >>> index.count( (0,0,100,100) )
  2L
  >>> sp.rollback()
  >>> #log( 'POST-ROLLBACK1' )
  >>>
  >>> noHousesInArea = index.count( (0,0,100,100) )
  >>> #log( 'Y', noHousesInArea, len(index.idToItem), struct.unpack( 'I', index.pageData[0][8:12] ) )
  >>> noHousesInArea
  2L
  >>> transaction.commit()
  >>>
  >>> #log( 'Z', len(index.idToItem), struct.unpack( 'I', index.pageData[0][8:12] ) )
  >>> housesInArea = list( index.intersection ( (0,0,100,100) ) )
  >>> #log( len(housesInArea) )
  >>> sorted( housesInArea ) == [house1, house2]
  True
  >>> closestHouse = list( index.nearest( (10,10), num_results = 1 ) )[0]
  >>> closestHouse == house1
  True
  >>> index.bounds
  [5.0, 5.0, 25.0, 25.0]
  >>> transaction.commit()
  >>>
  >>> index.index_doc( house6, House('Cottage #3', (10,10,25,25)) )
  >>> index.count( (0,0,100,100) )
  3L
  >>> transaction.abort()
  >>>
  >>> index.count( (0,0,100,100) )
  2L
  
Clear the index.

  >>> index.clear()
  >>> transaction.commit()
  >>> index.documentCount()
  0
  >>> index.count( (0,0,100,100) )
  0L

Run a little benchmark.

  >>> transaction.begin()
  <...>
  >>> # benchmark inserting 1000 random objects
  >>> #  note: This is not the smart way. If you want to insert many objects
  >>> #        at once, use the initialValuesGenerator.
  >>> #        It's nice for testing though since it will cause lots of writes.
  >>> import random
  >>> def generate(count, minX, minY, maxX, maxY):
  ...     for i in range(count):
  ...         x1, y1 = random.random() * minX, random.random() * minY
  ...         x2, y2 = x1 + random.random() * maxX, y1 + random.random() * maxY
  ...         yield House( 'Random house #%d' % i, (x1, y1, x2, y2) )
  >>>              
  >>> import time
  >>> start = time.clock()
  >>> noObjects = 1000
  >>> for i, house in enumerate(generate(noObjects, 1000, 1000, 1000, 1000)):
  ...     index.index_doc( i, house )
  >>> print 'Time to index 1000 houses', time.clock() - start
  Time to...
  >>> transaction.commit()
  >>> print 'Total time', time.clock() - start
  Total time...

Todo: test the index inside of a catalog. Too lazy now.

"""

import persistent
import transaction
import zope.interface

from zope.index.SpatialIndex import SpatialIndex

class IBounded(zope.interface.Interface):
    boundingBox = zope.interface.Attribute('boundingBox', 'A bounding box')

class House(persistent.Persistent):
    zope.interface.implements(IBounded)
    
    def __init__(self, name, boundingBox):
        persistent.Persistent.__init__( self )
        self.name = name
        self.boundingBox = boundingBox
    
def log(msg):
    print msg