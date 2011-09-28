from rtree.index import CustomStorage

class Storage(CustomStorage):
    """ A storage which saves the pages in a BTree mapping """
    def __init__(self, mapping, convertToInt = True):
        CustomStorage.__init__( self )
        self.mapping = mapping
        self.blockWrites = False
        self.convertToInt = convertToInt

    def create(self, returnError):
        """ Called when the storage is created on the C side """

    def destroy(self, returnError):
        """ Called when the storage is destroyed on the C side """

    def clear(self):
        """ Clear all our data """   
        self.mapping.clear()
        
    def convertPage(self, page):
        if self.convertToInt:
            page = int(page)
            if type(page) != int:
                raise OverflowError(page)
        return page

    def loadByteArray(self, page, returnError):
        """ Returns the data for page or returns an error """
        page = self.convertPage(page)
        #log( 'READ page:%s' % page )
        try:
            return self.mapping[page]
        except KeyError:
            returnError.contents.value = self.InvalidPageError

    def storeByteArray(self, page, data, returnError):
        """ Stores the data for page """
        page = self.convertPage(page)
        if self.blockWrites:
            #log( 'STORE BLOCKED page:%s' % page )
            return page
        if page == self.NewPage:
            newPageId = len(self.mapping)
            # TODO: should newPageId be random to better prevent ConflictErrors?
            #log( 'STORE NEW pageId:%s' % newPageId )
            self.mapping[newPageId] = data
            return newPageId
        else:
            #log( 'STORE pageId:%s' % page )
            if page not in self.mapping:
                returnError.value = self.InvalidPageError
                return 0
            self.mapping[page] = data
            #import struct
            #nodes = struct.unpack( 'I', self.mapping[0][8:12] ) if self.mapping else -1
            #log( 'STORE nodes:%s' % nodes )
            return page

    def deleteByteArray(self, page, returnError):
        """ Deletes a page """
        #log( 'DELETE pageId:%s' % page )
        page = self.convertPage(page)
        try:
            del self.mapping[page]
        except KeyError:
            returnError.contents.value = self.InvalidPageError

    hasData = property( lambda self: bool(self.mapping) )
    """ Returns true if this storage contains some data """   

