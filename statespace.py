class StateSpaceNode:
    def __init__(self, parent, path, depth, pawns={}):
        self.parent = parent
        self.int_position_pawns_caught = pawns
        self.path_id = path
        self.knight_state = 0
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
               len(self.int_position_pawns_caught - other.int_position_pawns_caught |
                   other.int_position_pawns_caught - self.int_position_pawns_caught) == 0 \
               and self.depth == other.depth
