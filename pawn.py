from graph import Vertex, Point
from main import CELLSPACING


class Pawn(Vertex):
    def __init__(self, x, y, dim, d=None):
        super(Pawn, self).__init__(x, y)
        self.steps_to_take = 0
        self.dim = dim
        if d is not None:
            self.direction = d
            if d is 1:
                # go left.
                self.steps_to_take = dim - y
            elif d is 2:
                self.steps_to_take = dim - x
            elif d is 3:
                self.steps_to_take = y
            else:
                self.steps_to_take = x
        else:
            if x > dim - x:
                # go left.
                self.direction = 4
                x_len = x
                self.steps_to_take = x_len
            else:
                # go right
                self.direction = 2
                x_len = dim - x
                self.steps_to_take = x_len
            if y > dim - y:
                # go down
                if y > x_len:
                    self.direction = 3
                    self.steps_to_take = y
            else:
                # go right
                if dim - y > x_len:
                    self.direction = 1
                    self.steps_to_take = dim - y

    def get_location(self):
        return self.point

    def get_position_in_steps(self, steps):
        x = self.point.x
        y = self.point.y
        c = 0
        n = 0
        nx = x
        ny = y
        if self.direction is 1:
            y = self.point.y + steps
            ny = y - 1
            c = (x, y)
            n = (nx, ny)
            if y > self.dim:
                c = None
            if ny > self.dim:
                n = None
        elif self.direction is 2:
            x = self.point.x + steps
            nx = x - 1
            c = (x, y)
            n = (nx, ny)
            if x >= self.dim - 1:
                c = None
            if nx >= self.dim - 1:
                n = None
        elif self.direction is 3:
            y = self.point.y - steps
            ny = y + 1
            c = (x, y)
            n = (nx, ny)
            if y <= 0:
                c = None
            if ny <= 0:
                n = None
        else:
            x = self.point.x - steps
            nx = x + 1
            c = (x, y)
            n = (nx, ny)
            if x <= 0:
                c = None
            if nx <= 0:
                n = None
        return c, n

    def move(self, max):
        self.steps_to_take -= 1
        if self.direction is 1:
            self.point.y += 1
            self.g_y += CELLSPACING
            self.point.set_graph_coord(self.point.g_x, self.g_y)
        elif self.direction is 2:
            self.point.x += 1
            self.g_x += CELLSPACING
            self.point.set_graph_coord(self.g_x, self.point.g_y)
        elif self.direction is 3:
            self.point.y -= 1
            self.g_x -= CELLSPACING
            self.point.set_graph_coord(self.point.g_x, self.g_y)
        else:
            self.point.x -= 1
            self.g_x -= CELLSPACING
            self.point.set_graph_coord(self.g_x, self.point.g_y)
        if self.point.x < 0 or self.point.y < 0 or self.point.y >= max or self.point.x >= max:
            return False
        else:
            return True

    def unmove(self, x, y):
        self.steps_to_take += 1
        if self.direction is 1:
            self.point.y -= 1
            self.g_y -= CELLSPACING
            self.point.set_graph_coord(self.point.g_x, self.g_y)
        elif self.direction is 2:
            self.point.x -= 1
            self.g_x -= CELLSPACING
            self.point.set_graph_coord(self.g_x, self.point.g_y)
        elif self.direction is 3:
            self.point.y += 1
            self.g_x += CELLSPACING
            self.point.set_graph_coord(self.point.g_x, self.g_y)
        else:
            self.point.x += 1
            self.g_x += CELLSPACING
            self.point.set_graph_coord(self.g_x, self.point.g_y)

    def get_next_move_position(self):
        if self.direction is 1:
            position = (self.point.x, self.point.y + 1)
        elif self.direction is 2:
            position = (self.point.x + 1, self.point.y)
        elif self.direction is 3:
            position = (self.point.x, self.point.y - 1)
        else:
            position = (self.point.x - 1, self.point.y)
        return position

    def get_steps_left(self):
        return self.steps_to_take

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
