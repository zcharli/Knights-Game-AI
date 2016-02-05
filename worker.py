import threading
import wx
import time

myEVT_MAKE_MOVE = wx.NewEventType()
EVT_MAKE_MOVE = wx.PyEventBinder(myEVT_MAKE_MOVE, 1)
myEVT_PAWN_MOVE = wx.NewEventType()
EVT_PAWN_MOVE = wx.PyEventBinder(myEVT_PAWN_MOVE, 1)


class MoveEvent(wx.PyCommandEvent):
    """Event to signal that a new move is ready"""

    def __init__(self, etype, eid, value=None):
        """Creates the event object"""
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def get_value(self):
        """Returns the value from the event.
        @return: the value of this event

        """
        return self._value


class ComputerPlayer(threading.Thread):
    def __init__(self, parent, value, canvas, mapping):
        """
        @param parent: The gui object that should receive the value
        @param value: value to 'calculate' to
        """
        threading.Thread.__init__(self)
        self._parent = parent
        self._goal_node = value
        self.int_to_coord_mappings = mapping
        self.boardCanvasSquares = canvas

    def run(self):
        """Overrides Thread.run. Don't call this directly its called internally
        when you call Thread.start().
        """
        print "spawned AI player"
        node_search = self._goal_node
        move_list = []
        while node_search.parent is not None:
            coord = self.int_to_coord_mappings[node_search.path_id]
            square = self.boardCanvasSquares[coord]
            move_list.append(square)
            node_search = node_search.parent

        for i in range(len(move_list) - 1):
            time.sleep(1)
            evt = MoveEvent(myEVT_MAKE_MOVE, -1, move_list.pop())
            wx.PostEvent(self._parent, evt)
            time.sleep(1)
            evt2 = MoveEvent(myEVT_PAWN_MOVE, -1, None)
            wx.PostEvent(self._parent, evt2)
