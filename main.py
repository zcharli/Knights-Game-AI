import wx

import random
from wx.lib.floatcanvas import NavCanvas, FloatCanvas

PLAYGAME = wx.NewId()
DFS = wx.NewId()
BFS = wx.NewId()
ASTAR = wx.NewId()
KNIGHTSBOARD = wx.NewId()

DEFAULT_SIZE = 20
NUMBER_OF_PAWNS = 4


class GameBoard(wx.Frame):
    def __init__(self, title):
        wx.Frame.__init__(self, None, title=title, pos=(150, 150), size=(800, 800))
        # Declare game variables
        self.boardGraph = {}
        self.pawns = set()
        self.knight = None
        # Import game resources
        self.txtDimensions = None
        self.knightIcon = wx.Image('images/knight.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.pawnIcon = wx.Image('images/pawn.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        # General game objects
        self._generate_starting_locations()
        # Generate game environment
        self.__do_layout()
        self._register_handlers()

    def __do_layout(self):
        sizer = wx.FlexGridSizer(cols=6, hgap=6, vgap=6)
        self.btnPlayGame = wx.Button(self, PLAYGAME, "Play Game")
        self.btnDFS = wx.Button(self, DFS, "Depth First Search")
        self.btnBFS = wx.Button(self, DFS, "Breadth First Search")
        self.btnAStar = wx.Button(self, DFS, "A* Search")
        lbl_dimensions = wx.StaticText(self, -1, "Grid Dimensions")
        self.txtDimensions = wx.TextCtrl(self, -1, str(DEFAULT_SIZE), size=(125, -1))
        sizer.AddMany([self.btnPlayGame, lbl_dimensions, self.txtDimensions,
                       self.btnBFS, self.btnDFS, self.btnAStar])
        self.screen = wx.BoxSizer(wx.VERTICAL)
        self.screen.Add(sizer, 0, wx.ALL, 25)
        self.boardCanvas = None
        self.SetSizer(self.screen)
        self.SetAutoLayout(True)

        # Build Board duplicate code, somehow I must do it in init
        dim = int(self.txtDimensions.GetValue())
        self._build_board_canvas(dim)
        self.screen.Add(self.boardCanvas, 0, wx.ALL, 25)

    def _register_handlers(self):
        wx.EVT_BUTTON(self, PLAYGAME, self._restart_game)

    def _build_board(self):
        if self.boardCanvas:
            self.boardCanvas.Destroy()
        dim = int(self.txtDimensions.GetValue())
        self._build_board_canvas(dim)
        self.screen.Add(self.boardCanvas, 0, wx.ALL, 25)
        self.screen.Layout()

    def _restart_game(self, event):
        self._build_board()

    def _generate_starting_locations(self):
        if self.txtDimensions:
            dim = int(self.txtDimensions.GetValue())
        else:
            dim = DEFAULT_SIZE
        # Generate random pawn location
        for i in range(NUMBER_OF_PAWNS):
            while True:
                x = random.randint(0 + int(dim / 10), dim - (int(dim / 10)))
                y = random.randint(0 + int(dim / 10), dim - (int(dim / 10)))
                d = random.randint(0, 3)
                pawn = Pawn(x, y, d)
                if pawn not in self.pawns:
                    self.pawns.add(pawn)
                    break
        # Generate location of knight
        x = random.randint(0 + int(dim / 4), dim - (int(dim / 4)))
        y = random.randint(0 + int(dim / 4), dim - (int(dim / 4)))
        self.knight = Knight(x, y)

    def _build_board_canvas(self, dimension):
        board_canvas = FloatCanvas.FloatCanvas(self, size=(800, 650),
                                               ProjectionFun=None,
                                               Debug=0,
                                               BackgroundColor="Black",
                                               )
        self.boardCanvas = board_canvas
        self.boardCanvas.Bind(wx.EVT_SIZE, self._on_size)
        self._2dArray = []
        w = 30
        dx = 32
        knight_icon = wx.Image('images/knight.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        pawn_icon = wx.Image('images/pawn.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()

        for i in range(dimension):
            row = []
            for j in range(dimension):
                fill_color = "White"
                current_position = (i, j)
                if i == 0 or i == dimension - 1 or j == 0 or j == dimension - 1:
                    fill_color = "Grey"
                if current_position in self.pawns:
                    square = self.boardCanvas.AddScaledBitmap(pawn_icon, (i * dx, j * dx),
                                                              (w),
                                                              Position='tl')
                elif i == self.knight.x and j == self.knight.y:
                    square = self.boardCanvas.AddScaledBitmap(knight_icon, (i * dx, j * dx),
                                                              (w),
                                                              Position='tl')
                else:
                    square = self.boardCanvas.AddRectangle((i * dx, j * dx), (w, w),
                                                           FillColor=fill_color, LineStyle=None)
                square.indexes = current_position
                row.append(0)
                self._2dArray.append(row)

    def _on_size(self, event):
        """
        re-zooms the canvas to fit the window
        """
        self.boardCanvas.ZoomToBB()
        event.Skip()


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __hash__(self):
        """Two vertices are the same if they have the same x and y coord"""
        return hash((self.x, self.y))

    def __str__(self):
        """Formats a string of this vertex to return"""
        return "(%d,%d)" % (self.x, self.y)

    def __eq__(self, other):
        """Two vertices are equal if they have the same x and y coord"""
        return self.x == other.x and self.y == other.y


class Vertex(object):
    """Vertex is defined to be just an X and Y coord on our plane"""

    def __init__(self, x, y):
        self.point = Point(x, y)
        self.visited = False

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


class Knight(Vertex):
    def __init__(self, x, y):
        super(Knight, self).__init__(x, y)
        self.x = x
        self.y = y


class Pawn(Vertex):
    def __init__(self, x, y, d):
        super(Pawn, self).__init__(x, y)
        self.direction = d

    def get_location(self):
        return self.point

    def __hash__(self):
        """Two vertices are the same if they have the same x and y coord"""
        return super(Vertex, self).__hash__()

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


class App(wx.App):
    def OnInit(self):
        frame = GameBoard('Knights Game')
        self.SetTopWindow(frame)
        frame.Show()
        return 1


if __name__ == "__main__":
    prog = App(0)
    prog.MainLoop()
