from zope.interface import implements, Attribute
from zope.schema import interfaces, Tuple

class IBounds(interfaces.ITuple):
    dimension = Attribute('''The dimension of the bounds, e.g. 2 or 3 for 2D and 3D respectively''')

class IPoint(IBounds):
    pass

class IBoundingBox(IBounds):
    pass


class Point(Tuple):
    implements(IPoint)

    def __init__(self, dimension, **kw):
        self.dimension = dimension
        super(Point, self).__init__( min_length = dimension, max_length = dimension, **kw)

class BoundingBox(Tuple):
    implements(IBoundingBox)

    def __init__(self, dimension, **kw):
        self.dimension = dimension
        super(BoundingBox, self).__init__( min_length = dimension * 2, max_length = dimension * 2, **kw)
