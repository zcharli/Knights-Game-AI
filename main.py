import wx

import pawn as pawn_model
import queue
import random
from wx.lib.floatcanvas import FloatCanvas
from graph import Point, Vertex, GraphConstructor
from knight import Knight

PLAYGAME = wx.NewId()
DFS = wx.NewId()
BFS = wx.NewId()
ASTAR = wx.NewId()
KNIGHTSBOARD = wx.NewId()

DEFAULT_SIZE = 10
NUMBER_OF_PAWNS = 4
CELLWIDTH = 30
CELLSPACING = 32
SPAWNPADDING = 3
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)


class GameBoard(wx.Frame):
    def __init__(self, title):
        wx.Frame.__init__(self, None, title=title, pos=(150, 150), size=(800, 800))
        # Declare game variables
        self._init_game_variables()
        self.txtDimensions = None
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
        self.isPlaying = True
        self.pawnsCaught = 0

    def _do_layout(self):
        sizer = wx.FlexGridSizer(cols=6, hgap=6, vgap=6)
        self.btnPlayGame = wx.Button(self, PLAYGAME, "Play Game")
        self.btnDFS = wx.Button(self, DFS, "Depth First Search")
        self.btnBFS = wx.Button(self, BFS, "Breadth First Search")
        self.btnAStar = wx.Button(self, ASTAR, "A* Search")
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
        wx.EVT_BUTTON(self, BFS, self._start_bfs)
        wx.EVT_BUTTON(self, DFS, self._start_dfs)
        wx.EVT_BUTTON(self, ASTAR, self._start_astar)

    def _start_bfs(self, event):
        num_moves_ascending = self.get_sorted_number_of_moves_left()
        cur_farthest_pawn = num_moves_ascending.pop()
        max_search_depth = self.pawns[num_moves_ascending[len(num_moves_ascending) - 1]].steps_to_take
        print "Starting BFS Search with max steps as " + str(max_search_depth)
        num_pawns_caught = 0
        current_depth = 0
        elements_to_depth_increase = 1
        next_elements_to_depth_increase = 0
        pawn_states = dict()
        for i in self.pawns:
            # current_pawns[self.pawns[i]] = self.pawns[i]
            pawn_states[self.pawns[i].get_position()] = i

        goals = dict()
        k_cur_position = self.knight.get_position()

        q = queue.Queue()
        q.insert([k_cur_position])
        # Emulate
        delete_pawns = set()
        while not q.is_empty():
            current_pawns = dict()
            cur_path = q.remove()

            (x, y) = cur_path[len(cur_path) - 1]

            cur_valid_moves = self.knight.get_valid_moves(x, y)
            pawn_caught = False

            if type(cur_path[0]) is not tuple:
                # return the state of this path based on pawns caught
                diff = set(self.pawns.keys()) - set(cur_path[0].keys())
                for i in diff:
                    current_pawns[self.pawns[i].get_position()] = self.pawns[i]

            else:
                for i in self.pawns:
                    current_pawns[self.pawns[i].get_position()] = self.pawns[i]

            # now pawn moves
            pawn_states = self.get_pawn_states(current_depth, current_pawns, self.dim)
            if (x, y) in pawn_states:
                pawn_caught = True
                pawn = pawn_states[(x, y)]
                farthest_pawn = cur_farthest_pawn.get_position_in_steps(current_depth)
                if farthest_pawn[0] is (x, y) or farthest_pawn[1] is (x, y):
                    cur_farthest_pawn = num_moves_ascending.pop()
                    max_search_depth = self.pawns[cur_farthest_pawn].steps_to_take
                    print "caught farthest pawn, reducing max steps to " + str(max_search_depth)
                pawns_caught_on_this_path = cur_path[0]
                j = 0
                if type(pawns_caught_on_this_path) is tuple:
                    # first pawn caught
                    cur_path.insert(0, dict())
                    for j in pawn:
                        cur_path[0][current_pawns[j]] = "caught: %s, %s at depth %s" % (x, y, current_depth)
                else:
                    for j in pawn:
                        if x == 6 and y==2 and current_pawns[j] == self.pawns[(4,2)]:
                            print "freeze"
                        cur_path[0][current_pawns[j]] = "caught: %s, %s at depth %s" % (x, y, current_depth)
                remove_collisions = False
                for i in cur_path[0].keys():
                    last = int(cur_path[0][i][-1:])
                    (t, z) = i.get_position()
                    if (t + last, z) not in cur_path:
                        print "collision "
                        print pawn
                        print pawn_states
                        print (x,y)
                        print "boooo"
                        remove_collisions = i
                if remove_collisions:
                    del cur_path[0][remove_collisions]

                num_pawns_caught += 1

            next_elements_to_depth_increase += len(cur_valid_moves)
            elements_to_depth_increase -= 1
            if elements_to_depth_increase == 0:
                current_depth += 1
                print current_depth
                if current_depth >= max_search_depth:
                    print "BFS search ended with " + str(max(goals.keys())) + " pawns caught"
                    print len(goals[max(goals.keys())])
                    return
                elements_to_depth_increase = next_elements_to_depth_increase
                next_elements_to_depth_increase = 0

            for i in cur_valid_moves:
                new_path = list(cur_path)
                new_path.append(i)
                if pawn_caught:
                    num_caught = len(new_path[0])
                    if num_caught in goals:
                        goals[num_caught].append(new_path)
                    else:
                        goals[num_caught] = [new_path]
                q.insert(new_path)

    def _start_dfs(self, event):
        print "Starting DFS Search"

    def _start_astar(self, event):
        print "Starting A Star"

    def _build_board(self):
        if self.boardCanvas:
            self.boardCanvas.Destroy()
        self._build_board_canvas(self.dim)
        self.screen.Add(self.boardCanvas, 0, wx.ALL, 25)
        self.screen.Layout()

    def _restart_game(self, event):
        self.dim = int(self.txtDimensions.GetValue())
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
        self.knight = Knight(5, 5, self.dim)
        # self.pawns[(8, 3)] = pawn_model.Pawn(8, 3, self.dim)
        # self.pawns[(4, 2)] = pawn_model.Pawn(4, 2, self.dim)
        # self.pawns[(3, 7)] = pawn_model.Pawn(3, 7, self.dim)
        # self.pawns[(6, 4)] = pawn_model.Pawn(6, 4, self.dim)
        self.pawns[(8, 3)] = pawn_model.Pawn(8, 3, self.dim, 2)
        self.pawns[(4, 2)] = pawn_model.Pawn(4, 2, self.dim, 2)
        self.pawns[(3, 7)] = pawn_model.Pawn(3, 7, self.dim, 2)
        self.pawns[(6, 4)] = pawn_model.Pawn(6, 4, self.dim, 2)
        self.validKnightMoves = self.knight.get_valid_moves()

        # x = random.randint(0 + int(self.dim / 4), self.dim - (int(self.dim / 4)))
        # y = random.randint(0 + int(self.dim / 4), self.dim - (int(self.dim / 4)))
        # self.knight = Knight(x, y, self.dim)
        # self.validKnightMoves = self.knight.get_valid_moves()
        # d = random.randint(0,3)
        # Generate random pawn location
        # for i in range(NUMBER_OF_PAWNS):
        #     while True:
        #         x = random.randint(SPAWNPADDING, self.dim - SPAWNPADDING)
        #         y = random.randint(SPAWNPADDING, self.dim - SPAWNPADDING)
        #         pawn = pawn_model.Pawn(x, y, self.dim)
        #         if pawn not in self.pawns and self.knight.get_position() not in self.pawns and pawn not in self.validKnightMoves:
        #             self.pawns[pawn.get_position()] = pawn
        #             break

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
                    square = self.boardCanvas.AddRectangle((i * CELLSPACING, j * CELLSPACING), (CELLWIDTH, CELLWIDTH),
                                                           FillColor=fill_color, LineStyle=None)
                    square = self.boardCanvas.AddScaledText(u"\u265F", (i * CELLSPACING + 15, j * CELLSPACING + 15),
                                                            CELLWIDTH + 5,
                                                            Color="Black", Position="cc")
                    # square = self.boardCanvas.AddScaledBitmap(pawn_icon, (i * CELLSPACING, j * CELLSPACING),
                    #                                           CELLWIDTH,
                    #                                           Position='bl')
                    pawn = self.pawns[current_position]
                    pawn.set_graph_coord(i * CELLSPACING, j * CELLSPACING)
                elif i == self.knight.get_x_coord() and j == self.knight.get_y_coord():
                    square = self.boardCanvas.AddRectangle((i * CELLSPACING, j * CELLSPACING), (CELLWIDTH, CELLWIDTH),
                                                           FillColor=fill_color, LineStyle=None)
                    square = self.boardCanvas.AddScaledText(u"\u265E", (i * CELLSPACING + 15, j * CELLSPACING + 14),
                                                            CELLWIDTH + 5,
                                                            Color="Black", Position="cc")
                    # square = self.boardCanvas.AddScaledBitmap(knight_icon, (i * CELLSPACING, j * CELLSPACING),
                    #                                           CELLWIDTH,
                    #                                           Position='bl')
                    self.knight.set_graph_coord(i * CELLSPACING, j * CELLSPACING)
                else:

                    square = self.boardCanvas.AddRectangle((i * CELLSPACING, j * CELLSPACING), (CELLWIDTH, CELLWIDTH),
                                                           FillColor=fill_color, LineStyle=None)
                loc = "(" + str(i) + "," + str(j) + ")"
                square = self.boardCanvas.AddScaledText(loc, ((i * CELLSPACING) + 10, j * CELLSPACING + 14),
                                                        5,
                                                        Color="Black", Position="cc")

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

        (t, v) = square.indexes.get_graph_coord()
        square = self.boardCanvas.AddRectangle((t, v), (CELLWIDTH, CELLWIDTH),
                                               FillColor="White", LineStyle=None)

        knight_new_square = self.boardCanvas.AddScaledText(u"\u265E", (t + 15, v + 14),
                                                           CELLWIDTH + 5,
                                                           Color="Black", Position="cc")
        # Create a new knight square at the square where the move was made
        # knight_new_square = self.boardCanvas.AddScaledBitmap(knight_icon, square.indexes.get_graph_coord(),
        #                                                      CELLWIDTH,
        #                                                      Position='bl')
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
            if square.indexes in self.pawns:
                print "caught a pawn"
                self.pawnsCaught += 1
                del self.pawns[square.indexes]
            self.clear_valid_moves()
            self.generate_new_valid_moves()
            self.move_pawns()
            self.boardCanvas.Draw(Force=True)

    def move_pawns(self):
        pawn_icon = wx.Image('images/pawn.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        pawns_to_delete = []
        pawns_that_moved_this_round = dict()
        for pawn in self.pawns:

            (i, j) = self.pawns[pawn].get_position()
            current_square = self.boardCanvasSquares[(i, j)]
            next_move = self.pawns[pawn].get_next_move_position()
            current_position = current_square.indexes

            if self.pawns[pawn].move(self.dim):
                (i, j) = self.pawns[pawn].get_position()
                if (i, j) == self.knight.point:
                    print "pawn walked into knight!"
                    pawns_to_delete.append(pawn)
                    self.boardCanvas.RemoveObject(current_square)
                    new_square = self.boardCanvas.AddRectangle(current_square.indexes.get_graph_coord(),
                                                               (CELLWIDTH, CELLWIDTH),
                                                               FillColor="White", LineStyle=None)
                    new_square.indexes = current_square.indexes
                    new_square.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.make_move)
                    self.boardCanvasSquares[new_square.indexes] = new_square
                else:
                    if next_move in pawns_that_moved_this_round.values():
                        self.pawns[pawn].unmove(i, j)
                        continue
                    else:
                        pawns_that_moved_this_round[pawn] = next_move

                    next_square = self.boardCanvasSquares[(i, j)]
                    self.boardCanvas.RemoveObject(next_square)
                    self.boardCanvas.RemoveObject(current_square)
                    # If the next square is a knight
                    if next_square.indexes in self.validKnightMoves:
                        fill_color = GREEN
                    elif self.check_location_is_edges(next_square.indexes):
                        fill_color = "Grey"
                    else:
                        fill_color = WHITE
                    square = self.boardCanvas.AddRectangle(next_square.indexes.get_graph_coord(),
                                                           (CELLWIDTH, CELLWIDTH),
                                                           FillColor=fill_color, LineStyle=None)
                    (t, v) = next_square.indexes.get_graph_coord()
                    pawn_new_square = self.boardCanvas.AddScaledText(u"\u265F", (t + 15, v + 15), CELLWIDTH + 5,
                                                                     Color="Black", Position="cc")
                    # pawn_new_square = self.boardCanvas.AddScaledBitmap(pawn_icon, next_square.indexes.get_graph_coord(),
                    #                                                    CELLWIDTH,
                    #                                                    Position='bl')
                    if current_square.indexes in self.validKnightMoves:
                        fill_color = GREEN
                    else:
                        fill_color = "White"
                    new_square = self.boardCanvas.AddRectangle(current_square.indexes.get_graph_coord(),
                                                               (CELLWIDTH, CELLWIDTH),
                                                               FillColor=fill_color, LineStyle=None)
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
                pawns_to_delete.append(pawn)
                self.boardCanvas.RemoveObject(current_square)
                new_square = self.boardCanvas.AddRectangle(current_square.indexes.get_graph_coord(),
                                                           (CELLWIDTH, CELLWIDTH),
                                                           FillColor="Grey", LineStyle=None)
                new_square.indexes = current_square.indexes
                new_square.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.make_move)
                self.boardCanvasSquares[new_square.indexes] = new_square

                print "a pawn has escaped!"

        for pawn in pawns_to_delete:
            print "deleted :"
            del self.pawns[pawn]
            if pawn in pawns_that_moved_this_round:
                del pawns_that_moved_this_round[pawn]

        for old_pos_key in pawns_that_moved_this_round:
            if self.pawns[old_pos_key] and self.pawns[old_pos_key] not in pawns_to_delete:
                self.pawns[pawns_that_moved_this_round[old_pos_key]] = self.pawns[old_pos_key]
                del self.pawns[old_pos_key]
            else:
                print "weird"
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

    def check_location_is_edges(self, point):
        if point.x is 0 or point.x is self.dim - 1:
            return True
        if point.y is 0 or point.y is self.dim - 1:
            return True
        return False

    def get_sorted_number_of_moves_left(self):
        list_pawns = []
        for i in self.pawns:
            list_pawns.append(self.pawns[i])
        return sorted(list_pawns, key=lambda x: x.steps_to_take, reverse=False)

    def get_pawn_states(self, steps, pawns, dim):
        pawn_states = dict()
        for i in pawns:
            (c, n) = pawns[i].get_position_in_steps(steps)
            if c is not None:
                if c not in pawn_states:
                    pawn_states[c] = [i]
                else:
                    pawn_states[c].append(i)
            if steps is not 0:
                if n is not None:
                    if n not in pawn_states:
                        pawn_states[n] = [i]
                    else:
                        pawn_states[n].append(i)
        return pawn_states


class App(wx.App):
    def OnInit(self):
        frame = GameBoard('Knights Game')
        self.SetTopWindow(frame)
        frame.Show()
        return 1


if __name__ == "__main__":
    prog = App(0)
    prog.MainLoop()



    # # check if i can make a move now and eat someone or else i will move the pawns
    # set_of_caught = cur_valid_moves.intersection(pawn_states)
    # for i in set_of_caught:
    #     if i in pawn_states:
    #         pawn_caught = True
    #         pawn = pawn_states[i]
    #         if cur_farthest_pawn.get_position_in_steps(current_depth)[0] is i:
    #             cur_farthest_pawn = num_moves_ascending.pop()
    #             max_search_depth = self.pawns[cur_farthest_pawn].steps_to_take
    #             print "caught farthest pawn, reducing max steps to " + str(max_search_depth)
    #
    #         pawns_caught_on_this_path = cur_path[0]
    #         if type(pawns_caught_on_this_path) is tuple:
    #             # first pawn caught
    #             cur_path.insert(0, set())
    #             for j in pawn:
    #                 cur_path[0].add(j)
    #         else:
    #             for j in pawn:
    #                 cur_path[0].add(j)
    #         #print "BFS caught a pawn on path while moving on it" + " ".join(str(e) for e in cur_path)
    #         num_pawns_caught += 1
