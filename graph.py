class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.g_x = 0
        self.g_y = 0

    def set_graph_coord(self, x, y):
        self.g_x = x
        self.g_y = y

    def get_graph_coord(self):
        return self.g_x, self.g_y

    def __hash__(self):
        """Two vertices are the same if they have the same x and y coord"""
        return hash((self.x, self.y))

    def __str__(self):
        """Formats a string of this vertex to return"""
        return "Point (%d,%d)" % (self.x, self.y)

    def __eq__(self, other):
        """Two vertices are equal if they have the same x and y coord"""
        if isinstance(other, Point):
            return self.x == other.x and self.y == other.y
        else:
            # elif type(other) is tuple:
            return self.x == other[0] and self.y == other[1]


class Vertex(object):
    """Vertex is defined to be just an X and Y coord on our plane"""

    def __init__(self, x, y):
        self.point = Point(x, y)
        self.visited = False
        self.g_x = 0
        self.g_y = 0

    def set_graph_coord(self, x, y):
        self.g_x = x
        self.g_y = y
        self.point.set_graph_coord(x, y)

    def get_graph_coord(self):
        return self.g_x, self.g_y

    def set_visited(self):
        """Sets the current node as visited"""
        self.visited = True

    def is_visited(self):
        """Checks the current node if it's been visited"""
        return self.visited

    def reset_visited(self):
        """Resets the node to it's non visited state"""
        self.visited = False

    def get_position(self):
        """Gets the current position of the node in (x,y) tuple form"""
        return self.point.x, self.point.y

    def __hash__(self):
        """Two vertices are the same if they have the same x and y coord"""
        return self.point.__hash__()

    def __str__(self):
        """Formats a string of this vertex to return"""
        return "(%d,%d)" % (self.x, self.y)

    def __eq__(self, other):
        """Two vertices are equal if they have the same x and y coord"""
        return self.point.x == other.point.x and self.point.y == other.point.y


class GraphConstructor(object):
    """Graph contructing object that parses a txt file into a graph"""

    def __init__(self, matrix):
        self.matrix = matrix
        self.adjacencyList = {}
        self.matrixHeight = len(matrix)
        self.matrixWidth = len(matrix[0])

    def getAdjacencyList(self):
        """Return the actual graph representation data structure"""
        return self.adjacencyList

    def isInvalidMove(self, x, y):
        """Checks to see if we really need to create a vertex at this (x,y)"""
        return self.matrix[x][y] == 'O'

    def addNeighbors(self, x, y):
        """Adds all the neighbors of (x,y) node whom are valid tiles to walk"""
        neighbors = []
        matrix = self.matrix
        if matrix is not None and len(matrix) > 0:
            if (x + 1 < self.matrixWidth - 1):
                if not self.isInvalidMove(x + 1, y):
                    vertex = Vertex(x + 1, y)
                    neighbors.append(vertex)
            if (x - 1 >= 0):
                if not self.isInvalidMove(x - 1, y):
                    vertex = Vertex(x - 1, y)
                    neighbors.append(vertex)
            if (y + 1 < self.matrixHeight - 1):
                if not self.isInvalidMove(x, y + 1):
                    vertex = Vertex(x, y + 1)
                    neighbors.append(vertex)
            if (y - 1 >= 0):
                if not self.isInvalidMove(x, y - 1):
                    vertex = Vertex(x, y - 1)
                    neighbors.append(vertex)
        return neighbors

    def parseGraph(self):
        """Break down the matrix into an adjacency list while finding the start
            and end node, O(n^2)
        """
        startNode = 0
        endNode = 0
        matrix = self.matrix
        for row, array in enumerate(matrix):
            for col, char in enumerate(array):
                if (char == 'R'):
                    startNode = Vertex(row, col)
                    self.adjacencyList[startNode] = self.addNeighbors(row, col)
                elif (char == '.'):
                    currNode = Vertex(row, col)
                    self.adjacencyList[currNode] = self.addNeighbors(row, col)
                elif (char == 'T'):
                    endNode = Vertex(row, col)
                    self.adjacencyList[endNode] = self.addNeighbors(row, col)
        return (startNode, endNode)
