"""
Storage
========

Exercise rtree's CustomStorage a bit.

  >>> settings = Property()
  >>> settings.writethrough = True
  >>> settings.buffering_capacity = 1
  >>> settings.pagesize = 100
  >>> settings.leaf_capacity = 20
  >>> settings.near_minimum_overlap_factor = 20
  >>> 
  >>> import random
  >>> def generate(count, minX, minY, maxX, maxY):
  ...     for i in range(count):
  ...         x1, y1 = random.random() * minX, random.random() * minY
  ...         x2, y2 = x1 + random.random() * maxX, y1 + random.random() * maxY
  ...         yield i, (x1, y1, x2, y2), None
  >>> 
  >>> storage = DictStorage()
  >>> r = Rtree( storage, properties = settings )
  >>> import time
  >>> start = time.clock()
  >>> for args in generate(10000, 100, 100, 100, 100):
  ...     r.insert( *args )
  >>> print 'Inserting 10000 items took ', time.clock() - start
  Inserting...
  >>> 
  >>> print '10 nearest points to (0,0) ', list(r.nearest((0, 0), 10))[0:10]
  10...
  >>> print 'Number of pages', len(storage.dict)
  Number...
  >>> 
  >>> storage.print_stores = True
  >>> for i in range(100000, 100010):
  ...   print '-' * 10
  ...   print '#%d' % i
  ...   item = list(generate(1, 100,100,100,100))[0]
  ...   r.add( *item )
  -----...
  >>> 
  >>> print 'Querying nearest object after inserting 100,000 more objects', list(r.nearest((0, 0), 1, objects = False))[0]
  Querying...
  >>> storage.print_stores = False
  >>> del r
"""

from rtree.index import Rtree, CustomStorage, Property

class DictStorage(CustomStorage):
    """ A simple storage which saves the pages in a python dictionary """
    def __init__(self):
        CustomStorage.__init__( self )
        self.clear()
        self.print_stores = False

    def create(self, returnError):
        """ Called when the storage is created on the C side """

    def destroy(self, returnError):
        """ Called when the storage is destroyed on the C side """

    def clear(self):
        """ Clear all our data """   
        self.dict = {}

    def loadByteArray(self, page, returnError):
        """ Returns the data for page or returns an error """   
        try:
            return self.dict[page]
        except KeyError:
            returnError.contents.value = self.InvalidPageError

    def storeByteArray(self, page, data, returnError):
        """ Stores the data for page """
        if self.print_stores:
            print 'STORE ', page
        if page == self.NewPage:
            newPageId = len(self.dict)
            self.dict[newPageId] = data
            return newPageId
        else:
            if page not in self.dict:
                returnError.value = self.InvalidPageError
                return 0
            self.dict[page] = data
            return page

    def deleteByteArray(self, page, returnError):
        """ Deletes a page """   
        try:
            del self.dict[page]
        except KeyError:
            returnError.contents.value = self.InvalidPageError

    hasData = property( lambda self: bool(self.dict) )
    """ Returns true if we contains some data """   
