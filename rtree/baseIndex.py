from rtree.index import Rtree, Property
import transaction
from persistent import Persistent
from persistent.dict import PersistentDict
import BTrees

from datamanager import DataManager
from storage import Storage
import zope.interface
from zope.index import interfaces as zopeindexinterfaces

    
class SpatialIndex(Persistent):
    ''' A spatial index. You can insert objects with their coordinates and later
         perform queries on the index.
    '''
    zope.interface.implements(
        zopeindexinterfaces.IInjection,
        zopeindexinterfaces.IStatistics,
        zopeindexinterfaces.IIndexSearch,
        )

    default_family = BTrees.family32
    
    def __init__(self, settings = {}, initialValuesGenerator = None):
        ''' Init. settings provide many means to customize the spatial tree.
            E.g. setting leaf_capacity and near_minimum_overlap_factor to "good"
            values can help to reduce the possibility of write conflict errors.
            
            Below is a list of the currently available properties. For more info
            about these and other properties see the rtree docs and/or code.
            
                writethrough
                buffering_capacity
                pagesize
                leaf_capacity
                near_minimum_overlap_factor
                type
                variant
                dimension
                index_capacity
                index_pool_capacity
                point_pool_capacity
                region_pool_capacity
                tight_mbr
                fill_factor
                split_distribution_factor
                tpr_horizon
                reinsert_factor
                
            If you supply an initialValuesGenerator you can build a spatial index
            from initial values. This is much faster than doing repeated insert()s.
        '''
        Persistent.__init__( self )
        self.family = settings.pop( 'family', self.default_family )
        self.settings = PersistentDict( settings )
        self.pageData = self.family.IO.BTree()             # here we save the actual rtree data in
        self.idToCoordinates = self.family.IO.BTree()      # we need to know the coordinates for each objectid to be able to delete it

        # this creates the tree and creates header and root pages
        self._getTree( initialValuesGenerator )

    def index_doc(self, docid, coordinates):
        ''' Inserts object with bounds into this index. Returns the added item. '''
        self._registerDataManager()
        self.tree.add( docid, coordinates )
        self.idToCoordinates[docid] = coordinates
        
    def unindex_doc(self, docid):
        ''' Deletes an item from this index '''
        self._registerDataManager()
        try:
            coordinates = self.idToCoordinates.pop( docid )
        except KeyError:
            # docid was not indexed
            return
        self.tree.delete( docid, coordinates )

    def clear(self):
        self._clearBuffer(True)
        del self._v_tree
        self.pageData.clear()
        self.idToCoordinates.clear()        
        self._getTree()     # this creates the tree and creates header and root pages

    def documentCount(self):
        """See interface IStatistics"""        
        return len(self.idToCoordinates)    # Could use BTree.Len() instead for better performance

    def wordCount(self):
        """See interface IStatistics"""
        return 0                            # no meaning really
        
    def apply(self, queryName, *args, **keys):
        queryFunc = getattr( self, queryName )
        generator = queryFunc( *args, **keys )
        return self.family.IF.Set( generator )
    # query methods
    
    def count(self, coordinates):
        ''' Counts the number of objects within coordinates '''
        self._registerDataManager()
        count = self.tree.count( coordinates )
        if self.family == BTrees.family32:
            count = int(count)
        return count
    
    def intersection(self, coordinates):
        ''' Returns all docids which are within the given bounds.
        '''
        self._registerDataManager()
        tree = self.tree
        if self.family == BTrees.family32:
            for id in tree.intersection( coordinates, objects = False ):
                yield int(id)
        else:            
            for id in tree.intersection( coordinates, objects = False ):
                yield id

    def nearest(self, coordinates, num_results = 1):
        ''' Returns the num_results docids which are closest to coordinates
        '''
        self._registerDataManager()
        tree = self.tree
        if self.family == BTrees.family32:
            for id in tree.nearest( coordinates, num_results, objects = False ):
                yield int(id)
        else:            
            for id in tree.nearest( coordinates, num_results, objects = False ):
                yield id

    def leaves(self):
        ''' Returns all leaves in the tree. A leaf is a tuple (id, child_ids, bounds) '''
        self._registerDataManager()
        for leaf in self.tree.leaves():
            yield leaf

    def get_bounds(self, coordinate_interleaved = None):
        ''' Returns the bounds of the whole tree '''
        self._registerDataManager()
        return self.tree.get_bounds( coordinate_interleaved )
    
    bounds = property( get_bounds )
    
    # implementation helpers
    
    def _clearBuffer(self, blockWrites):
        tree = getattr( self, '_v_tree', None )
        if not tree:
            return
        if blockWrites:
            tree.customstorage.blockWrites = True
        #log( 'PRE-CLEAR blockWrites:%s tree:%s bounds:%s' % ( blockWrites, self.tree, self.bounds ) )
        #log( 'PRE-CLEAR' )
        tree.clearBuffer()
        #log( 'POST-CLEAR bounds:%s' % self.bounds )
        #log( 'POST-CLEAR' )
        if blockWrites:
            tree.customstorage.blockWrites = False

    def _registerDataManager(self):
        ''' This registers a custom data manager to flush all the buffers when
             they are dirty. '''
        registered = getattr( self, '_v_dataManagerRegistered', False )
        if registered:
            return
        self._v_dataManagerRegistered = True
        
        # haha, this is really ugly, but zodb's transaction module sorts
        #  data managers only on commit(). That's not good for us, our data
        #  manager's savepoint/rollback/abort calls need to be executed before
        #  the connection's savepoint/rollback/abort.
        t = transaction.get()
        org_join = t.join
        def join(resource):
            org_join( resource )
            t._resources = sorted( t._resources, transaction._transaction.rm_cmp )
        t.join = join
        t.join( DataManager(self) )
        
    def _unregisterDataManager(self):
        self._v_dataManagerRegistered = False

    def _getTree(self, initialValuesGenerator = None):
        ''' Creates the r-tree if it is not already created yet and returns it '''
        tree = getattr( self, '_v_tree', None )
        if not tree:
            # create r-tree property object
            properties = Property()
            settings = getattr(self, 'settings', None)
            if not settings:
                raise ValueError('invalid spatial index')
            # check interleaved setting
            interleaved = settings.pop('interleaved', True)
            for name, value in settings.items():
                if not hasattr( properties, name ):
                    raise ValueError( 'Invalid setting "%s"' % name )
                setattr( properties, name, value )
            # create r-tree storage object
            storage = Storage( self.pageData, convertToInt = (self.family == BTrees.family32) )
            # create r-tree
            if not initialValuesGenerator:
                tree = Rtree( storage, properties = properties, interleaved = interleaved )
            else:
                tree = Rtree( storage, initialValuesGenerator, properties = properties, interleaved = interleaved )
            self._v_tree = tree
        else:
            if initialValuesGenerator:
                raise ValueError(initialValuesGenerator)
            
        return tree
        
    tree = property( _getTree )
    

