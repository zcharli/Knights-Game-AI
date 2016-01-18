import wx

import random
from wx.lib.floatcanvas import NavCanvas, FloatCanvas
from graph import Point, Vertex, GraphConstructor

PLAYGAME = wx.NewId()
DFS = wx.NewId()
BFS = wx.NewId()
ASTAR = wx.NewId()
KNIGHTSBOARD = wx.NewId()

DEFAULT_SIZE = 20
NUMBER_OF_PAWNS = 4
CELLWIDTH = 30
CELLSPACING = 32

GREEN = (0, 255, 0)
WHITE = (255, 255, 255)


class GameBoard(wx.Frame):
    def __init__(self, title):
        wx.Frame.__init__(self, None, title=title, pos=(150, 150), size=(800, 800))
        # Declare game variables
        self._init_game_variables()
        # General game objects
        self._generate_starting_locations()
        # Generate game environment
        self._do_layout()
        self._register_handlers()
        self.generate_new_valid_moves()

    def _init_game_variables(self):
        self.boardGraph = {}
        self.validKnightMoves = set()  # all the possible valid moves (x,y)
        self.validKnightMoveSquares = set()  # all the possible valid square moves
        self.boardCanvasSquares = dict()  # all the squares on the grid
        self.pawns = {}
        self.knight = None
        self.txtDimensions = None
        self.isPlaying = True
        self.pawnsCaught = 0

    def _do_layout(self):
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
        self.dim = int(self.txtDimensions.GetValue())
        self._build_board_canvas(self.dim)
        self.screen.Add(self.boardCanvas, 0, wx.ALL, 25)

    def _register_handlers(self):
        wx.EVT_BUTTON(self, PLAYGAME, self._restart_game)

    def _build_board(self):
        if self.boardCanvas:
            self.boardCanvas.Destroy()
        self._build_board_canvas(self.dim)
        self.screen.Add(self.boardCanvas, 0, wx.ALL, 25)
        self.screen.Layout()

    def _restart_game(self, event):
        self._init_game_variables()
        self._generate_starting_locations()
        self._build_board()
        self.generate_new_valid_moves()

    def _generate_starting_locations(self):
        if self.txtDimensions:
            self.dim = int(self.txtDimensions.GetValue())
        else:
            self.dim = DEFAULT_SIZE
        print "Generating board for dimension " + str(self.dim)
        # Generate location of knight
        x = random.randint(0 + int(self.dim / 4), self.dim - (int(self.dim / 4)))
        y = random.randint(0 + int(self.dim / 4), self.dim - (int(self.dim / 4)))
        self.knight = Knight(x, y, self.dim)
        self.validKnightMoves = self.knight.get_valid_moves()
        # Generate random pawn location
        for i in range(NUMBER_OF_PAWNS):
            while True:
                x = random.randint(5, self.dim - 5)
                y = random.randint(5, self.dim - 5)
                d = random.randint(0, 3)
                pawn = Pawn(x, y, d)
                if pawn not in self.pawns and self.knight not in self.pawns and pawn not in self.validKnightMoves:
                    self.pawns[pawn.get_position()] = pawn
                    break

    def _build_board_canvas(self, dimension):
        board_canvas = FloatCanvas.FloatCanvas(self, size=(800, 650),
                                               ProjectionFun=None,
                                               Debug=0,
                                               BackgroundColor="Black",
                                               )
        self.boardCanvas = board_canvas
        self.boardCanvas.Bind(wx.EVT_SIZE, self._on_size)

        knight_icon = wx.Image('images/knight.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        pawn_icon = wx.Image('images/pawn.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        for i in range(dimension):
            for j in range(dimension):
                fill_color = "White"
                current_position = (i, j)
                point = Point(i, j)
                point.set_graph_coord(i * CELLSPACING, j * CELLSPACING)

                if i == 0 or i == dimension - 1 or j == 0 or j == dimension - 1:
                    fill_color = "Grey"
                if current_position in self.pawns:
                    square = self.boardCanvas.AddScaledBitmap(pawn_icon, (i * CELLSPACING, j * CELLSPACING),
                                                              CELLWIDTH,
                                                              Position='bl')
                    pawn = self.pawns[current_position]
                    pawn.set_graph_coord(i * CELLSPACING, j * CELLSPACING)
                elif i == self.knight.get_x_coord() and j == self.knight.get_y_coord():
                    square = self.boardCanvas.AddScaledBitmap(knight_icon, (i * CELLSPACING, j * CELLSPACING),
                                                              CELLWIDTH,
                                                              Position='bl')
                    self.knight.set_graph_coord(i * CELLSPACING, j * CELLSPACING)
                else:
                    square = self.boardCanvas.AddRectangle((i * CELLSPACING, j * CELLSPACING), (CELLWIDTH, CELLWIDTH),
                                                           FillColor=fill_color, LineStyle=None)

                self.boardCanvasSquares[point] = square
                square.indexes = point
                square.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.make_move)

    def add_knight_to_position(self, square):
        knight_icon = wx.Image('images/knight.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        # Remove old squares: Knight and legal (green) move square
        self.boardCanvas.RemoveObject(square)
        # Save the previous knight position to create new white square
        knight_prev_coord = self.knight.get_graph_coord()
        knight_prev_position = self.knight.get_position()
        square_prev_position = square.indexes
        k_square = self.boardCanvasSquares[knight_prev_position]
        k_prev_indexes = k_square.indexes
        self.boardCanvas.RemoveObject(k_square)

        # Create a new knight square at the square where the move was made
        knight_new_square = self.boardCanvas.AddScaledBitmap(knight_icon, square.indexes.get_graph_coord(),
                                                             CELLWIDTH,
                                                             Position='bl')
        knight_new_square.indexes = square_prev_position
        knight_new_square.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.make_move)
        self.boardCanvasSquares[knight_new_square.indexes] = knight_new_square
        square_prev_coord = square_prev_position.get_graph_coord()
        self.knight.set_graph_coord(square_prev_coord[0], square_prev_coord[1])
        self.knight.set_position(square_prev_position.x, square_prev_position.y)

        # Create a blank square ( can be green since we can always move back)
        k_prev_square = self.boardCanvas.AddRectangle(k_prev_indexes.get_graph_coord(), (CELLWIDTH, CELLWIDTH),
                                                      FillColor="White", LineStyle=None)
        k_prev_square.indexes = k_prev_indexes
        k_prev_square.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.make_move)
        self.boardCanvasSquares[k_prev_square.indexes] = k_prev_square

    def generate_new_valid_moves(self):
        self.validKnightMoves = self.knight.get_valid_moves()
        for coords in self.validKnightMoves:
            if coords in self.boardCanvasSquares:
                self.color_square(self.boardCanvasSquares[coords], GREEN)
        self.boardCanvas.Draw(True)

    def clear_valid_moves(self):
        for coords in self.validKnightMoves:
            self.color_square(self.boardCanvasSquares[coords], WHITE)
        self.boardCanvas.Draw()
        self.validKnightMoves = {}

    def make_move(self, square):
        # print "player made a move square hit:" + str(square.indexes)
        if square.indexes in self.validKnightMoves:
            self.add_knight_to_position(square)
            self.clear_valid_moves()
            self.generate_new_valid_moves()
            if square.indexes in self.pawns:
                print "caught a pawn"
                self.pawnsCaught += 1
                del self.pawns[square.indexes]
            self.move_pawns()
            self.boardCanvas.Draw(Force=True)

    def move_pawns(self):
        pawn_icon = wx.Image('images/pawn.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        pawn_to_delete = None
        for pawn in self.pawns:
            (i, j) = self.pawns[pawn].get_position()
            current_square = self.boardCanvasSquares[(i, j)]
            if self.pawns[pawn].move(self.dim):
                (i, j) = self.pawns[pawn].get_position()
                next_square = self.boardCanvasSquares[(i, j)]
                self.boardCanvas.RemoveObject(next_square)
                self.boardCanvas.RemoveObject(current_square)
                # If the next square is a knight
                pawn_new_square = self.boardCanvas.AddScaledBitmap(pawn_icon, next_square.indexes.get_graph_coord(),
                                                                   CELLWIDTH,
                                                                   Position='bl')
                new_square = self.boardCanvas.AddRectangle(current_square.indexes.get_graph_coord(),
                                                           (CELLWIDTH, CELLWIDTH),
                                                           FillColor="White", LineStyle=None)
                pawn_new_square.indexes = next_square.indexes
                new_square.indexes = current_square.indexes
                new_square.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.make_move)
                pawn_new_square.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.make_move)
                self.boardCanvasSquares[new_square.indexes] = new_square
                self.boardCanvasSquares[pawn_new_square.indexes] = pawn_new_square
                self.pawns[pawn].set_position(i, j)
                graph_coords = next_square.indexes.get_graph_coord()
                self.pawns[pawn].set_graph_coord(graph_coords[0], graph_coords[1])
            else:
                pawn_to_delete = pawn
                self.boardCanvas.RemoveObject(current_square)
                new_square = self.boardCanvas.AddRectangle(current_square.indexes.get_graph_coord(),
                                                           (CELLWIDTH, CELLWIDTH),
                                                           FillColor="Grey", LineStyle=None)
                new_square.indexes = current_square.indexes
                new_square.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.make_move)
                self.boardCanvasSquares[new_square.indexes] = new_square

                print "a pawn has escaped!"

        if pawn_to_delete:
            del self.pawns[pawn_to_delete]
        self.boardCanvas.Draw()

    def is_valid_knight_move(self, point_tuple):
        return point_tuple in self.validKnightMoves

    def _on_size(self, event):
        """
        re-zooms the canvas to fit the window
        """
        self.boardCanvas.ZoomToBB()
        event.Skip()

    def color_square(self, square, color, force=False):
        square.SetFillColor(color)
        if force:
            self.boardCanvas.Draw(True)


class Knight(Vertex):
    def __init__(self, x, y, dim):
        super(Knight, self).__init__(x, y)
        self.dim = dim

    def get_valid_moves(self):
        valid_move_set = set()

        max_x = max_y = self.dim - 2
        min_x = min_y = 1
        x = self.get_x_coord()
        y = self.get_y_coord()
        if x - 2 >= min_x:
            # can go full left
            if y + 1 < max_y:
                valid_move_set.add((x - 2, y + 1))
            if y - 1 > min_y:
                valid_move_set.add((x - 2, y - 1))
        elif x - 1 >= min_x:
            # can only go partially left
            if y + 2 < max_y:
                valid_move_set.add((x - 1, y + 2))
            if y - 2 > min_y:
                valid_move_set.add((x - 1, y - 2))
        if x + 2 <= max_x:
            # can go full right
            if y + 1 < max_y:
                valid_move_set.add((x + 2, y + 1))
            if y - 1 > min_y:
                valid_move_set.add((x + 2, y - 1))
        elif x + 1 <= max_x:
            # can go partially right
            if y + 2 < max_y:
                valid_move_set.add((x + 1, y + 2))
            if y - 2 > min_y:
                valid_move_set.add((x + 1, y - 2))
        if y + 2 <= max_y:
            if x + 1 < max_x:
                valid_move_set.add((x + 1, y + 2))
            if x - 1 > min_x:
                valid_move_set.add((x - 1, y + 2))
        elif y + 1 <= max_y:
            if x - 2 > min_x:
                valid_move_set.add((x - 2, y + 1))
            if x + 2 < max_x:
                valid_move_set.add((x + 2, y + 1))
        if y - 2 >= min_y:
            if x + 1 < max_x:
                valid_move_set.add((x + 1, y - 2))

            if x - 1 > min_x:
                valid_move_set.add((x - 1, y - 2))
        elif y - 1 >= min_y:
            if x - 2 > min_x:
                valid_move_set.add((x - 2, y - 1))
            if x + 2 < max_x:
                valid_move_set.add((x + 2, y - 1))
        print len(valid_move_set)
        return valid_move_set

    def get_x_coord(self):
        return self.point.x

    def get_y_coord(self):
        return self.point.y

    def set_position(self, x, y):
        self.point.x = x
        self.point.y = y

    def set_graph_coord(self, x, y):
        self.g_x = x
        self.g_y = y
        self.point.set_graph_coord(x, y)

    def get_graph_coord(self):
        return self.g_x, self.g_y


class Pawn(Vertex):
    def __init__(self, x, y, d):
        super(Pawn, self).__init__(x, y)
        self.direction = d

    def get_location(self):
        return self.point

    def move(self, max):
        if self.direction is 1:
            self.point.y += 1
            self.g_y += CELLSPACING
        elif self.direction is 2:
            self.point.x += 1
            self.g_x += CELLSPACING
        elif self.direction is 3:
            self.point.y -= 1
            self.g_x -= CELLSPACING
        else:
            self.point.x -= 1
            self.g_x -= CELLSPACING
        if self.point.x < 0 or self.point.y < 0 or self.point.y >= max or self.point.x >= max:
            return False
        else:
            return True

    def set_position(self, x, y):
        self.point.x = x
        self.point.y = y

    def set_graph_coord(self, x, y):
        self.g_x = x
        self.g_y = y
        self.point.set_graph_coord(x, y)

    def get_graph_coord(self):
        return self.g_x, self.g_y

    def __hash__(self):
        """Two vertices are the same if they have the same x and y coord"""
        return hash((self.point.x, self.point.y))

    def __str__(self):
        """Formats a string of this vertex to return"""
        return "Pawn at (%d,%d)" % (self.point.x, self.point.y)

    def __eq__(self, other):
        """Two vertices are equal if they have the same x and y coord"""
        if isinstance(other, Pawn):
            return self.point.x == other.point.x and self.point.y == other.point.y
        elif isinstance(other, Point):
            return self.point.x == other.x and self.point.y == other.y
        else:
            # elif type(other) is tuple:
            return self.point.x == other[0] and self.point.y == other[1]


class App(wx.App):
    def OnInit(self):
        frame = GameBoard('Knights Game')
        self.SetTopWindow(frame)
        frame.Show()
        return 1


if __name__ == "__main__":
    prog = App(0)
    prog.MainLoop()
