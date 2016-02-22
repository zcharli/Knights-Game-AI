from graph import Vertex


class Knight(Vertex):
    def __init__(self, x, y, dim):
        super(Knight, self).__init__(x, y)
        self.dim = dim
        self.coord_to_int_mappings = None

    def set_coord_mappings(self, mappings, backwards_mapping):
        self.coord_to_int_mappings = mappings
        self.int_to_coord_mappings = backwards_mapping

    def get_valid_moves(self, int=None,fx=0, fy=0):
        valid_move_set = set()
        max_x = max_y = self.dim - 2
        min_x = min_y = 1
        if int is not None:
            x,y = self.int_to_coord_mappings[int]
        elif fx == 0 or fy == 0:
            x = self.get_x_coord()
            y = self.get_y_coord()
        else:
            x = fx
            y = fy
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
        if int:
            int_set = set()
            for i in valid_move_set:
                int_set.add(self.coord_to_int_mappings[i])
            return int_set
        else:
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
