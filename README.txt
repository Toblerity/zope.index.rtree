=========================
anima.core.content.index.spatial
=========================

The package `anima.core.content.index.spatial` provides a 2d, 3d, n-d spatial index. 
It builts upon the python rtree package which has a fast underlying C library.
Furthermore, this index integrates fully with the zodb, including transactions.

You can index bounding boxes and points currently.

.. contents::

Quick example
=============

The index is compatible with zope.catalog and thus can be used like it.

This example shows how to index a few simple 2d objects.

Import boilerplate stuff ::

  >>> import persistent
  >>> import transaction
  >>> import zope.interface
  >>> from anima.core.content.index.spatial.index import SpatialIndex
  >>> import BTrees        
  
Quickly setup a zodb ::

  >>> import ZODB.tests.util
  >>> db = ZODB.tests.util.DB()
  >>> dbconn = db.open()
  >>> dbroot = dbconn.root()

Create a house. A house has a bounding box and thus is a spatial object which can be indexed ::

  >>> class House(persistent.Persistent):
  ...     def __init__(self, name, boundingBox):
  ...         persistent.Persistent.__init__( self )
  ...         self.name = name
  ...         self.boundingBox = boundingBox

Finally create the index ::

  >>> settings = dict( dimension = 2, leaf_capacity = 20, pagesize = 4096, near_minimum_overlap_factor = 20, writethrough = False, buffering_capacity = 100, family = BTrees.family64 )
  >>> dbroot['index'] = index = SpatialIndex( field_name = 'boundingBox', interface = None, field_callable=False, settings = settings )
  >>> transaction.commit()
  
And add some sample content to the index, by default bounding box is like (minx, miny, maxx, maxy) ::

  >>> index.index_doc( 123, House('Mansion', (5,5,25,25)) )
  >>> index.documentCount()
  1
  
Note that you can use the interleaved = False setting if you want to use bounding boxes like (minx, maxx, miny, maxy).
  
Now perform some queries on the index. Count all objects within the (0,0,100,100) bounding box ::

  >>> index.count( (0,0,100,100) )
  1L
  
Find all objects within the (0,0,100,100) bounding box ::

  >>> list( index.intersection( (0,0,100,100) ) )
  [123L]
  
Find the single nearest object to (0,0) ::

  >>> list( index.nearest( (0,0), num_results = 1 ) )
  [123L]

Use the apply() function ::

  >>> list( index.apply( 'intersection', (0,0,1,1) ) )
  []
  
Get the bounds of the whole index ::

  >>> index.bounds
  [5.0, 5.0, 25.0, 25.0]


We're done, let's unindex the document for illustrative purposes ::

  >>> index.unindex_doc( 123 )
  >>> index.documentCount()
  0

You can also clear the index ::

  >>> index.clear()

  
To make this really useful, use the IIntId util to map ids to actual objects. This is already done if you use the index
within zope.catalog.


Old info from original announcement, some of the following info might be dated
===============================================================================

Where to get it?
=================

See attachment. It's still a very rough alpha version, don't use in  
production. The attached test case works only in my own testing  
environment, but you can see how the spatial index can be used.

What can it do?
=================

You can insert your objects into the index along with a set of  
coordinates. These coordinates can be 2d, 3d and even n-d. The  
coordinates can be points or bounding boxes. The data is paged to the  
database as needed, so you can create much bigger indices than would fit  
in memory. Later you can then query the index for objects in a given area  
or for the n-nearest objects to a certain point.

The underlying tree of the index is quite flexible, for example there are  
special variants of the tree which are "very well suited suited for mobile  
systems where queries on moving objects are common" [1]. The individual  
variants can also be customized extensively, e.g. you can change the leaf  
size, split factor, buffering and many more parameters. That's useful to  
minimize ConflictErrors.

For detailed information, please see http://pypi.python.org/pypi/Rtree ,  
http://trac.gispython.org/spatialindex,  
http://anandmu.googlepages.com/comparison3finalreport.pdf and the  
spatialindex sources.

How does it work?
==================

I've gone and extended the rtree c api a bit so it supports custom  
storages. This means you need the latest svn version if you want to test.  
I have windows binaries ready for those interested.

Then I wrote the code you see in spatialIndex.py. When you add an object  
to a SpatialIndex it generates a new entry with a random 64-bit integer  
and stores the mapping id->object into an LOBTree. The individual tree  
leaves are paged and stored via a custom rtree storage as binary data in  
an LOBTree which maps pageId->pageData.

A custom data manager makes sure the tree's buffers are flushed at  
transaction boundaries (commit/abort/savepoint/rollback). This ensures the  
spatial index is fully transactional.

All the heavy lifting is done by the rtree and spatialindex libraries.  
They are very well written in C++, so performance for the queries  
themselves is quite high. The slow part is fetching pages from ZODB (ZEO),  
but since objects which are located close to each other are likely to end  
up in the same leafs and pages, you take the "fetch from db" hit only for  
the first access and subsequent accesses will be cached (unless you are  
also writing a lot).

For concrete examples, please the tests.

Known issues?
==============

cleanness: The code is littered with ugly log statements. I've had a few  
problems with the data manager (see below).

ConflictErrors: If you have a tree with very few leaves (e.g. huge leave  
size or small number of objects) conflict errors will occur rather often,  
because the objects are saved to the same page. You can fine tune this by  
adjusting the rtree parameters (e.g. leaf_capacity, index_capacity,  
pagesize and near_minimum_overlap_factor).

data manager: I had to hook the transaction's join() method in a very ugly  
way, see the other post I made today for more about this.

entry ids: Entry ids are 64-bit. For very large trees this might be  
insufficient to prevent collisions. This is checked however and an error  
is raised when this happens.

performance: In some quick tests I did the index performed very well for  
my needs. You might want to write your own benchmark if you plan to really  
hammer the index.

packaging: I don't plan to create a package for this as I don't see much  
point in adding yet another package to the clutter of packages surrounding  
zodb.


References:
=============

[1] http://anandmu.googlepages.com/comparison3finalreport.pdf