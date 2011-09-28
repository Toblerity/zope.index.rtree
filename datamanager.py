import sys

class DataManager(object):
    transaction_manager = None

    class Savepoint(object):
        def __init__(self, dataManager):
            self.dataManager = dataManager
            self.dataManager.clearBuffer( blockWrites = False )
        
        def rollback(self):
            self.dataManager.clearBuffer( blockWrites = True )

    def __init__(self, spatialIndex):
        self.spatialIndex = spatialIndex
        
    def clearBuffer(self, blockWrites):
        self.spatialIndex._clearBuffer( blockWrites )
        
    def unregister(self):
        self.spatialIndex._unregisterDataManager()

    def abort(self, transaction):
        self.clearBuffer( blockWrites = True )
        self.unregister()
    
    def savepoint(self):
        return self.Savepoint(self)

    def tpc_begin(self, transaction):
        self.clearBuffer( blockWrites = False )

    def commit(self, transaction):
        pass

    def tpc_vote(self, transaction):
        pass

    def tpc_finish(self, transaction):
        self.unregister()

    def tpc_abort(self, transaction):
        self.unregister()

    def sortKey(self):
        return -sys.maxint
