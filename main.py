import wx

import pawn as pawn_model
from knight import Knight
import sys
from statespace import StateSpaceNode, StateSpaceNodeDFS, StateSpaceNodeAStar
import copy
from collections import deque
import random
import worker
from wx.lib.floatcanvas import FloatCanvas
from graph import Point
from math import sqrt
from heapq import heappush, heappop
import wx.lib.newevent

PLAYGAME = wx.NewId()
DFS = wx.NewId()
BFS = wx.NewId()
ASTAR = wx.NewId()
KNIGHTSBOARD = wx.NewId()

SLEEP_TIME_SECONDS = 0
DEFAULT_SIZE = 20
NUMBER_OF_PAWNS = 4
CELLWIDTH = 30
CELLSPACING = 32
SPAWNPADDING = 2
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)


class GameBoard(wx.Frame):
    def __init__(self, title):
        wx.Frame.__init__(self, None, title=title, pos=(150, 150), size=(800, 800))
        # Declare game variables
        self._init_game_variables()
        self.txtDimensions = None
        self.txtPawns = None
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
        self.coord_to_int_mappings = dict()
        self.int_to_coord_mappings = dict()

    def _do_layout(self):
        sizer = wx.FlexGridSizer(rows=2, cols=6, hgap=6, vgap=6)
        self.btnPlayGame = wx.Button(self, PLAYGAME, "Play Game")
        self.btnDFS = wx.Button(self, DFS, "Depth First Search")
        self.btnBFS = wx.Button(self, BFS, "Breadth First Search")
        self.btnAStar = wx.Button(self, ASTAR, "A* Search")
        lbl_dimensions = wx.StaticText(self, -1, "Grid Dimensions")
        lblPawns = wx.StaticText(self, -1, "# Pawns")
        self.txtDimensions = wx.TextCtrl(self, -1, str(DEFAULT_SIZE), size=(125, -1))
        self.txtPawns = wx.TextCtrl(self, -1, str(NUMBER_OF_PAWNS), size=(125, -1))
        sizer.AddMany([self.btnPlayGame, lbl_dimensions, self.txtDimensions, lblPawns, self.txtPawns])
        sizer.AddStretchSpacer()
        sizer.AddMany([self.btnBFS, self.btnDFS, self.btnAStar])
        self.screen = wx.BoxSizer(wx.VERTICAL)
        self.screen.Add(sizer, 0, wx.ALL, 25)
        self.boardCanvas = None
        self.SetSizer(self.screen)
        self.SetAutoLayout(True)

        # Build Board duplicate code, somehow I must do it in init
        self.dim = int(self.txtDimensions.GetValue())
        self.number_of_pawns = int(self.txtPawns.GetValue())
        self._build_board_canvas(self.dim)
        self.screen.Add(self.boardCanvas, 0, wx.ALL, 25)

    def _register_handlers(self):
        wx.EVT_BUTTON(self, PLAYGAME, self._restart_game)
        wx.EVT_BUTTON(self, BFS, self._start_bfs)
        wx.EVT_BUTTON(self, DFS, self._start_dfs)
        wx.EVT_BUTTON(self, ASTAR, self._start_astar)
        self.Bind(worker.EVT_MAKE_MOVE, self.make_artificial_move)
        self.Bind(worker.EVT_PAWN_MOVE, self.make_artificial_pawn_move)

    def _start_bfs(self, event):
        print "Starting BFS Search"
        # Tell our knight about the mappings
        self.knight.set_coord_mappings(self.coord_to_int_mappings, self.int_to_coord_mappings)

        # Map out pawns out for search, as we represent each location of the pawn with integer
        # From int to pawn -> get pawn starting location #, convert coord, use self.pawns to retrieve
        pawn_int_mappings = set()
        pawn_int_possible_locations_mapping = dict()
        pawns_on_the_board = []
        for pawn in self.pawns:
            # Map all the possible ending locations to point back to the same pawn
            s, e = self.pawns[pawn].get_tuple_possible_moves()
            starting_int_location_representation = self.coord_to_int_mappings[s]
            ending_int_location_representation = self.coord_to_int_mappings[e]
            pawn_int_mappings.add(starting_int_location_representation)
            pawn_int_possible_locations_mapping[starting_int_location_representation] = \
                [starting_int_location_representation]
            # It is possible that two pawns end up at the same "second" location, but not first
            # If this happens, we catch them all.
            if ending_int_location_representation in pawn_int_possible_locations_mapping:
                pawn_int_possible_locations_mapping[ending_int_location_representation] \
                    .append(starting_int_location_representation)
            else:
                pawn_int_possible_locations_mapping[ending_int_location_representation] = \
                    [starting_int_location_representation]
            pawns_on_the_board.append(starting_int_location_representation)

        # Depth control variables
        current_depth = 0
        elements_to_depth_increase = 1
        next_elements_to_depth_increase = 0

        # Our queue, using the deque implementation
        q = deque()
        root_node = StateSpaceNode(None, self.coord_to_int_mappings[self.knight.get_position()], 0,
                                   set(pawns_on_the_board))
        q.append(root_node)
        goal_not_reached = True
        goal_node = None

        # All the states that ever passed.
        state_history = set()

        # Build the tree
        while len(q) != 0 and goal_not_reached:
            current_node = q.popleft()
            pawn_caught = False
            current_position = current_node.path_id
            pawns_caught = []

            # Check if we caught a pawn at this position
            if current_position in pawn_int_possible_locations_mapping:
                pawn_caught = True
                pawns_at_position = pawn_int_possible_locations_mapping[current_position]
                # Generally only 1 element at this position, sometimes two, with max NUMBER_OF_PAWNS
                for pawn in pawns_at_position:
                    # This is an O(1) operation here
                    if pawn in current_node.int_position_pawns_caught:
                        # Map them pawn caught back to the pawn at starting position
                        pawns_caught.extend(pawn_int_possible_locations_mapping[current_position])

            # Get a set of all possible int mappings of coordinates
            cur_valid_moves = self.knight.get_valid_moves(current_position, True)

            # Calculate the depth dynamically
            next_elements_to_depth_increase += len(cur_valid_moves)
            elements_to_depth_increase -= 1
            if elements_to_depth_increase == 0:
                current_depth += 1
                print current_depth
                elements_to_depth_increase = next_elements_to_depth_increase
                next_elements_to_depth_increase = 0

            # Build new Nodes for all the discovered valid moves
            for path_id in cur_valid_moves:
                new_node = StateSpaceNode(current_node, path_id, current_depth,
                                          set(copy.deepcopy(current_node.int_position_pawns_caught)))
                if pawn_caught:
                    for pawn in pawns_caught:
                        # This is an O(1) operation, do not expect it to run much more than n^NUMBER_OF_PAWNS
                        if pawn in new_node.int_position_pawns_caught:
                            new_node.int_position_pawns_caught.remove(pawn)
                    if len(new_node.int_position_pawns_caught) == 0:
                        goal_not_reached = False
                        goal_node = new_node
                        break
                if new_node in state_history:
                    continue
                else:
                    state_history.add(new_node)
                q.append(new_node)
        print "Search finished"
        k = goal_node
        while k.parent is not None:
            print self.int_to_coord_mappings[k.path_id]
            k = k.parent
        player = worker.ComputerPlayer(self, goal_node, self.boardCanvasSquares, self.int_to_coord_mappings)
        player.start()

    def make_artificial_move(self, evt):
        # self.make_move(evt.get_value())
        square = evt.get_value()
        # print "player made a move square hit:" + str(square.indexes)
        # print self.knight.get_position()
        if square.indexes in self.validKnightMoves:
            self.add_knight_to_position(square)
            current_pos = dict(zip(self.pawns.values(), self.pawns.keys()))
            if square.indexes in current_pos:
                print "caught a pawn"
                self.pawnsCaught += 1
                del self.pawns[current_pos[square.indexes]]
            self.clear_valid_moves()
            self.generate_new_valid_moves()
            self.boardCanvas.Draw(Force=True)

    def make_artificial_pawn_move(self, evt):
        square = evt.get_value()
        self.move_pawns()
        self.boardCanvas.Draw(Force=True)

    def _start_dfs(self, event):
        print "Starting BFS Search"
        # Tell our knight about the mappings
        self.knight.set_coord_mappings(self.coord_to_int_mappings, self.int_to_coord_mappings)

        # Map out pawns out for search, as we represent each location of the pawn with integer
        # From int to pawn -> get pawn starting location #, convert coord, use self.pawns to retrieve
        pawn_int_mappings = set()
        pawn_int_possible_locations_mapping = dict()
        pawns_on_the_board = []
        for pawn in self.pawns:
            # Map all the possible ending locations to point back to the same pawn
            s, e = self.pawns[pawn].get_tuple_possible_moves()
            starting_int_location_representation = self.coord_to_int_mappings[s]
            ending_int_location_representation = self.coord_to_int_mappings[e]
            pawn_int_mappings.add(starting_int_location_representation)
            pawn_int_possible_locations_mapping[starting_int_location_representation] = \
                [starting_int_location_representation]
            # It is possible that two pawns end up at the same "second" location, but not first
            # If this happens, we catch them all.
            if ending_int_location_representation in pawn_int_possible_locations_mapping:
                pawn_int_possible_locations_mapping[ending_int_location_representation] \
                    .append(starting_int_location_representation)
            else:
                pawn_int_possible_locations_mapping[ending_int_location_representation] = \
                    [starting_int_location_representation]
            pawns_on_the_board.append(starting_int_location_representation)

        # Depth control variables
        current_depth = 0
        elements_to_depth_increase = 1
        next_elements_to_depth_increase = 0

        # Our queue, using the deque implementation
        q = []
        root_node = StateSpaceNodeDFS(None,
                                      self.coord_to_int_mappings[self.knight.get_position()],
                                      0,
                                      pawns_on_the_board)
        q.append(root_node)
        goal_not_reached = True
        goal_node = None

        # All the states that ever passed.
        state_history = set()

        # Build the tree
        while len(q) != 0 and goal_not_reached:
            current_node = q.pop()
            pawn_caught = False
            current_position = current_node.path_id
            pawns_caught = []

            # Check if we caught a pawn at this position
            if current_position in pawn_int_possible_locations_mapping:
                pawn_caught = True
                pawns_at_position = pawn_int_possible_locations_mapping[current_position]
                # Generally only 1 element at this position, sometimes two, with max NUMBER_OF_PAWNS
                for pawn in pawns_at_position:
                    # This is an O(1) operation here
                    if pawn in current_node.int_position_pawns_caught:
                        # Map them pawn caught back to the pawn at starting position
                        pawns_caught.extend(pawn_int_possible_locations_mapping[current_position])

            # Get a set of all possible int mappings of coordinates
            cur_valid_moves = self.knight.get_valid_moves(current_position, True)
            # Calculate the depth dynamically
            next_elements_to_depth_increase += len(cur_valid_moves)
            elements_to_depth_increase -= 1
            if elements_to_depth_increase == 0:
                current_depth += 1
                print current_depth
                elements_to_depth_increase = next_elements_to_depth_increase
                next_elements_to_depth_increase = 0
            # DFS will require some smart choices if possible
            captureable_pawns = cur_valid_moves.intersection(pawn_int_possible_locations_mapping)
            if len(captureable_pawns) > 0:
                temp_valid_moves = []
                for path in cur_valid_moves:
                    if path not in captureable_pawns:
                        temp_valid_moves.append(path)
                temp_valid_moves.extend(captureable_pawns)
                cur_valid_moves = temp_valid_moves

            # Build new Nodes for all the discovered valid moves
            for path_id in cur_valid_moves:
                new_node = StateSpaceNodeDFS(current_node, path_id, current_node.depth + 1,
                                             set(copy.deepcopy(current_node.int_position_pawns_caught)))
                if pawn_caught:
                    for pawn in pawns_caught:
                        # This is an O(1) operation, do not expect it to run much more than n^NUMBER_OF_PAWNS
                        if pawn in new_node.int_position_pawns_caught:
                            new_node.int_position_pawns_caught.remove(pawn)
                    if len(new_node.int_position_pawns_caught) == 0:
                        goal_not_reached = False
                        goal_node = new_node
                        break
                if new_node in state_history:
                    continue
                else:
                    state_history.add(new_node)

                q.append(new_node)
        print "Search finished"
        k = goal_node
        while k.parent is not None:
            print self.int_to_coord_mappings[k.path_id]
            k = k.parent
        player = worker.ComputerPlayer(self, goal_node, self.boardCanvasSquares, self.int_to_coord_mappings)
        player.start()

    def _start_astar(self, event):
        print "Starting A Star"
        # Tell our knight about the mappings
        self.knight.set_coord_mappings(self.coord_to_int_mappings, self.int_to_coord_mappings)

        # Map out pawns out for search, as we represent each location of the pawn with integer
        # From int to pawn -> get pawn starting location #, convert coord, use self.pawns to retrieve
        pawn_int_mappings = set()
        self.pawn_int_possible_locations_mapping = dict()
        self.pawn_int_possible_move_mapping = dict()
        pawns_on_the_board = []
        for pawn in self.pawns:
            # Map all the possible ending locations to point back to the same pawn
            s, e = self.pawns[pawn].get_tuple_possible_moves()
            starting_int_location_representation = self.coord_to_int_mappings[s]
            ending_int_location_representation = self.coord_to_int_mappings[e]
            pawn_int_mappings.add(starting_int_location_representation)
            self.pawn_int_possible_locations_mapping[starting_int_location_representation] = \
                [starting_int_location_representation]
            # It is possible that two pawns end up at the same "second" location, but not first
            # If this happens, we catch them all.
            if ending_int_location_representation in self.pawn_int_possible_locations_mapping:
                self.pawn_int_possible_locations_mapping[ending_int_location_representation] \
                    .append(starting_int_location_representation)
            else:
                self.pawn_int_possible_locations_mapping[ending_int_location_representation] = \
                    [starting_int_location_representation]
            self.pawn_int_possible_move_mapping[starting_int_location_representation] = \
                [ending_int_location_representation, starting_int_location_representation]
            pawns_on_the_board.append(starting_int_location_representation)

        # Depth control variables
        current_depth = 0
        elements_to_depth_increase = 1
        next_elements_to_depth_increase = 0

        heap = []

        root_node = StateSpaceNodeAStar(None,
                                        self.coord_to_int_mappings[self.knight.get_position()],
                                        0,
                                        set(pawns_on_the_board))
        heappush(heap, root_node)
        goal_not_reached = True
        goal_node = None

        # All the states that ever passed.
        state_history = set()
        nodes_generated = 0
        nodes_total_generated = 0
        while len(heap) != 0 and goal_not_reached:
            current_node = heappop(heap)
            pawn_caught = False
            current_position = current_node.path_id
            pawns_caught = []

            # Check if we caught a pawn at this position
            if current_position in self.pawn_int_possible_locations_mapping:
                pawn_caught = True
                pawns_at_position = self.pawn_int_possible_locations_mapping[current_position]
                # Generally only 1 element at this position, sometimes two, with max NUMBER_OF_PAWNS
                for pawn in pawns_at_position:
                    # This is an O(1) operation here
                    if pawn in current_node.int_position_pawns_caught:
                        # Map them pawn caught back to the pawn at starting position
                        pawns_caught.extend(self.pawn_int_possible_locations_mapping[current_position])

            # Get a set of all possible int mappings of coordinates
            cur_valid_moves = self.knight.get_valid_moves(current_position, True)

            # # DFS will require some smart choices if possible
            # captureable_pawns = cur_valid_moves.intersection(pawn_int_possible_locations_mapping)
            # if len(captureable_pawns) > 0:
            #     temp_valid_moves = []
            #     for path in cur_valid_moves:
            #         if path not in captureable_pawns:
            #             temp_valid_moves.append(path)
            #     temp_valid_moves.extend(captureable_pawns)
            #     cur_valid_moves = temp_valid_moves

            qpawns, qmoves = self.quadrantize(current_node.path_id, current_node.int_position_pawns_caught,
                                              cur_valid_moves)
            for path_id in cur_valid_moves:
                nodes_total_generated += 1
                new_node = StateSpaceNodeAStar(current_node, path_id, current_node.depth + 1,
                                               copy.deepcopy(current_node.int_position_pawns_caught))
                # Update the new node's priority
                quadrant_val = self.calc_quadrant(path_id, qpawns, qmoves, current_node.int_position_pawns_caught)
                distance_val = 0
                if quadrant_val == sys.maxint:
                    continue
                elif quadrant_val != 0:
                    distance_val = self.calc_distance(path_id, qpawns[qmoves[path_id]])
                priority = current_node.depth + 1 + quadrant_val + distance_val
                if priority > sys.maxint:
                    continue
                new_node.priority = priority
                if pawn_caught:
                    for pawn in pawns_caught:
                        # This is an O(1) operation, do not expect it to run much more than n^NUMBER_OF_PAWNS
                        if pawn in new_node.int_position_pawns_caught:
                            new_node.int_position_pawns_caught.remove(pawn)
                    if len(new_node.int_position_pawns_caught) == 0:
                        goal_not_reached = False
                        goal_node = new_node
                        print "A Star goal reached"
                        break
                if new_node in state_history:
                    continue
                else:
                    state_history.add(new_node)
                    nodes_generated += 1
                heappush(heap, new_node)
        print "After generating a total %d nodes when using just %d states, the search finished" % \
              (nodes_total_generated, nodes_generated)
        k = goal_node
        while k.parent is not None:
            print self.int_to_coord_mappings[k.path_id]
            k = k.parent
        player = worker.ComputerPlayer(self, goal_node, self.boardCanvasSquares, self.int_to_coord_mappings)
        player.start()

    def calc_quadrant(self, path, qpawns, qmoves, pawns_alive):
        quadrant = qmoves[path]
        num_pawns_in_quadrant = len(qpawns[quadrant])
        if num_pawns_in_quadrant == 0:
            return sys.maxint
        alive_location_mapping = set()
        for i in pawns_alive:
            mapping = self.pawn_int_possible_move_mapping[i]
            alive_location_mapping.add(mapping[0])
            alive_location_mapping.add(mapping[1])
        if path in alive_location_mapping:
            return 0
        else:
            return num_pawns_in_quadrant

    def calc_distance(self, next_pos, pawn_positions):
        least_distance = sys.maxint
        (nx, ny) = self.int_to_coord_mappings[next_pos]
        d = 1

        for i in pawn_positions:
            if next_pos in self.pawn_int_possible_move_mapping[i]:
                d = 0.5
            (x, y) = self.int_to_coord_mappings[i]
            euclidean_distance = d * sqrt((x - nx) ** 2 + (y - ny) ** 2)
            if euclidean_distance < least_distance:
                least_distance = euclidean_distance
        return least_distance

    def quadrantize(self, cur_pos, pawn_on_board, cur_valid_moves):
        quadrant_pawns = {1: [], 2: [], 3: [], 4: []}
        quadrant_moves = dict()
        (px, py) = self.int_to_coord_mappings[cur_pos]

        for i in pawn_on_board:
            (x, y) = self.int_to_coord_mappings[i]
            if x >= px and y >= py:
                quadrant_pawns[1].append(i)
            elif x <= px and y >= py:
                quadrant_pawns[2].append(i)
            elif x <= px and y <= py:
                quadrant_pawns[3].append(i)
            elif x >= px and y <= py:
                quadrant_pawns[4].append(i)
            else:
                print "Oh no! A pawn position skipped the quadrant test"
        for i in cur_valid_moves:
            (x, y) = self.int_to_coord_mappings[i]
            if x >= px and y >= py:
                quadrant_moves[i] = 1
            elif x <= px and y >= py:
                quadrant_moves[i] = 2
            elif x <= px and y <= py:
                quadrant_moves[i] = 3
            elif x >= px and y <= py:
                quadrant_moves[i] = 4
            else:
                print "Oh no! A move position skipped the quadrant test"
        return quadrant_pawns, quadrant_moves

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
        if self.txtPawns:
            self.number_of_pawns = int(self.txtPawns.GetValue())
        else:
            self.number_of_pawns = NUMBER_OF_PAWNS
        print "Generating board for dimension " + str(self.dim) + " with " + str(self.number_of_pawns) + " pawns."

        # Generate location of knight
        x = random.randint(int(self.dim / 4), self.dim - (int(self.dim / 4)))
        y = random.randint(int(self.dim / 4), self.dim - (int(self.dim / 4)))
        self.knight = Knight(x, y, self.dim)
        self.validKnightMoves = self.knight.get_valid_moves()
        d = random.randint(0, 3)
        # Generate random pawn location
        for i in range(self.number_of_pawns):
            while True:
                x = random.randint(SPAWNPADDING, self.dim - SPAWNPADDING)
                y = random.randint(SPAWNPADDING, self.dim - SPAWNPADDING)
                pawn = pawn_model.Pawn(x, y, self.dim, d)
                if pawn not in self.pawns and self.knight.get_position() not in self.pawns and pawn not in self.validKnightMoves:
                    self.pawns[pawn.get_position()] = pawn
                    break
                else:
                    print x, y

    def _build_board_canvas(self, dimension):
        board_canvas = FloatCanvas.FloatCanvas(self, size=(800, 650),
                                               ProjectionFun=None,
                                               Debug=0,
                                               BackgroundColor="Black",
                                               )
        self.boardCanvas = board_canvas
        self.boardCanvas.Bind(wx.EVT_SIZE, self._on_size)
        mapping_num = 1
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
                    pawn = self.pawns[current_position]
                    pawn.set_graph_coord(i * CELLSPACING, j * CELLSPACING)
                elif i == self.knight.get_x_coord() and j == self.knight.get_y_coord():
                    square = self.boardCanvas.AddRectangle((i * CELLSPACING, j * CELLSPACING), (CELLWIDTH, CELLWIDTH),
                                                           FillColor=fill_color, LineStyle=None)
                    square = self.boardCanvas.AddScaledText(u"\u265E", (i * CELLSPACING + 15, j * CELLSPACING + 14),
                                                            CELLWIDTH + 5,
                                                            Color="Black", Position="cc")
                    self.knight.set_graph_coord(i * CELLSPACING, j * CELLSPACING)
                else:

                    square = self.boardCanvas.AddRectangle((i * CELLSPACING, j * CELLSPACING), (CELLWIDTH, CELLWIDTH),
                                                           FillColor=fill_color, LineStyle=None)
                # loc = "(" + str(i) + "," + str(j) + ")"
                # square = self.boardCanvas.AddScaledText(loc, ((i * CELLSPACING) + 10, j * CELLSPACING + 14),
                #                                        5,
                #                                        Color="Black", Position="cc")
                self.coord_to_int_mappings[current_position] = mapping_num
                self.int_to_coord_mappings[mapping_num] = current_position
                mapping_num += 1
                self.boardCanvasSquares[point] = square
                square.indexes = point
                square.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.make_move)

    def add_knight_to_position(self, square):
        # Remove old squares: Knight and legal (green) move square
        try:
            delete_square = self.boardCanvasSquares[square.indexes]
            self.boardCanvas.RemoveObject(delete_square)
        except:
            print "point not in canvas"
            print square.indexes
        # Save the previous knight position to create new white square
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
        print self.knight.get_position()
        # print "player made a move square hit:" + str(square.indexes)
        if square.indexes in self.validKnightMoves:
            self.add_knight_to_position(square)
            current_pos = dict(zip(self.pawns.values(), self.pawns.keys()))
            if square.indexes in current_pos:
                print "caught a pawn"
                self.pawnsCaught += 1
                del self.pawns[current_pos[square.indexes]]
            self.clear_valid_moves()
            self.generate_new_valid_moves()
            self.move_pawns()
            self.boardCanvas.Draw(Force=True)

    def move_pawns(self):
        pawns_to_delete = []
        pawns_that_moved_this_round = dict()

        for pawn in self.pawns:
            (i, j) = self.pawns[pawn].get_position()
            current_square = self.boardCanvasSquares[(i, j)]
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

    def get_pawn_states(self, steps, pawns):
        pawn_states = dict()
        for i in pawns:
            c, n = pawns[i].get_position_in_steps(steps)
            # if c is not None:
            #     if c not in pawn_states:
            #         pawn_states[c] = [i]
            #     else:
            #         pawn_states[c].append(i)
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
