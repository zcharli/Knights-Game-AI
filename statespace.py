class StateSpaceNode(object):
    def __init__(self, parent, path, depth, pawns={}):
        self.parent = parent
        self.int_position_pawns_caught = pawns
        self.path_id = path
        self.depth = depth
        self.hash = hash((self.path_id, self.depth, tuple(self.int_position_pawns_caught)))

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        has_value = True
        # for p in self.int_position_pawns_caught:
        #     if p not in other.int_position_pawns_caught:
        #         has_value = False
        return self.path_id == other.path_id and \
               len(self.int_position_pawns_caught - other.int_position_pawns_caught) == 0 and len(
                   other.int_position_pawns_caught - self.int_position_pawns_caught) == 0 \
               and self.depth == other.depth


class StateSpaceNodeDFS(StateSpaceNode):
    def __init__(self, parent, path, depth, pawns={}, last_move=None):
        super(StateSpaceNodeDFS, self).__init__(parent, path, depth, pawns)
        self.last_move = last_move
        self.hash = hash((self.path_id, tuple(self.int_position_pawns_caught), self.last_move))

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        has_value = True
        # for p in self.int_position_pawns_caught:
        #     if p not in other.int_position_pawns_caught:
        #         has_value = False
        return self.path_id == other.path_id and \
               len(self.int_position_pawns_caught - other.int_position_pawns_caught) == 0 and len(
                   other.int_position_pawns_caught - self.int_position_pawns_caught) == 0 \
               and self.last_move == other.last_move


class StateSpaceNodeAStar(StateSpaceNode):
    def __init__(self, parent, path, depth, pawns={}, priority=0, cost=0):
        super(StateSpaceNodeAStar, self).__init__(parent, path, depth, pawns)
        self.priority = priority
        self.hash = hash((self.path_id, tuple(self.int_position_pawns_caught)))
        self.cost = cost

    def __cmp__(self, other):
        return cmp(self.priority, other.priority)

    def __index__(self):
        return int(self.priority)

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        has_value = True
        # for p in self.int_position_pawns_caught:
        #     if p not in other.int_position_pawns_caught:
        #         has_value = False
        return self.path_id == other.path_id and \
               len(self.int_position_pawns_caught - other.int_position_pawns_caught) == 0 and len(
                   other.int_position_pawns_caught - self.int_position_pawns_caught) == 0 \
               #and self.depth == other.depth
               #and self.priority == other.priority and self.depth == other.depth
