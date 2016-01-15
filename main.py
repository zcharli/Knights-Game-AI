import wx
import random
from wx.lib.floatcanvas import NavCanvas, FloatCanvas

PLAYGAME = wx.NewId()
DFS = wx.NewId()
BFS = wx.NewId()
ASTAR = wx.NewId()
KNIGHTSBOARD = wx.NewId()


class GameBoard(wx.Frame):
    def __init__(self, title):
        wx.Frame.__init__(self, None, title=title, pos=(150, 150), size=(800, 800))
        self.__do_layout()

    def __do_layout(self):
        sizer = wx.FlexGridSizer(cols=6, hgap=6, vgap=6)
        self.btnPlayGame = wx.Button(self, PLAYGAME, "Restart Game")
        self.btnDFS = wx.Button(self, DFS, "Depth First Search")
        self.btnBFS = wx.Button(self, DFS, "Breadth First Search")
        self.btnAStar = wx.Button(self, DFS, "A* Search")
        lblDimensions = wx.StaticText(self, -1, "Grid Dimensions")
        self.txtDimensions = wx.TextCtrl(self, -1, "30", size=(125, -1))

        sizer.AddMany([self.btnPlayGame, lblDimensions, self.txtDimensions,
                       self.btnBFS, self.btnDFS, self.btnAStar])

        self.screen = wx.BoxSizer(wx.VERTICAL)
        self.screen.Add(sizer, 0, wx.ALL, 25)
        self.board = None
        self.SetSizer(self.screen)
        self.SetAutoLayout(True)
        self._register_handlers()
        self._play_game(self.txtDimensions.GetValue())

    def _register_handlers(self):
        wx.EVT_BUTTON(self, PLAYGAME, self._play_game)

    def _play_game(self, event):
        if self.board:
            print "Removing Board"
            self._remove_board();
        self.board = self._build_board_canvas(int(self.txtDimensions.GetValue()))
        self.screen.Add(self.board)
        self.Refresh()

    def _remove_board(self):
        self.board.Clear()
        self.boardCanvas.ClearAll()
        self.screen.Hide(self.board)
        self.screen.Remove(self.board)
        self.board = None

    def _build_board_canvas(self, dimension):
        box = wx.BoxSizer(wx.VERTICAL)
        board_canvas = FloatCanvas.FloatCanvas(self, size=(800, 700),
                                              ProjectionFun=None,
                                              Debug=0,
                                              BackgroundColor="Black",
                                              )
        self.boardCanvas = board_canvas
        self.boardCanvas.Bind(wx.EVT_SIZE, self._on_size)
        w = 30
        dx = 32
        for i in range(dimension):
            for j in range(dimension):
                landable_square = self.boardCanvas.AddRectangle((i * dx, j * dx), (w, w),
                                                                FillColor="White", LineStyle=None)
                landable_square.indexes = (i, j)

        box.Add(board_canvas)
        return box

    def _on_size(self, event):
        """
        re-zooms the canvas to fit the window
        """
        self.boardCanvas.ZoomToBB()
        event.Skip()


class KnightsBoard(wx.Panel):
    def __init__(self, parent, dimension):
        wx.Panel.__init__(self, parent)
        self.dimension = dimension
        box = wx.BoxSizer(wx.VERTICAL)

        boardCanvas = FloatCanvas.FloatCanvas(self, size=(800, 800),
                                              ProjectionFun=None,
                                              Debug=0,
                                              BackgroundColor="Black",
                                              )
        self.boardCanvas = boardCanvas
        self.boardCanvas.Bind(wx.EVT_SIZE, self._on_size)
        # build the squares:
        w = 2
        dx = 4
        for i in range(9):
            for j in range(9):
                landableSquare = self.boardCanvas.AddRectangle((i * dx, j * dx), (w, w),
                                                               FillColor="White", LineStyle=None)
                landableSquare.indexes = (i, j)
                # outline = self.boardCanvas.AddRectangle((i * dx, j * dx), (w, w),
                #                                         FillColor=None,
                #                                         LineWidth=4,
                #                                         LineColor='Red',
                #                                         LineStyle=None)
                # landableSquare.outline = outline

        self.SetSizer(box)
        self.Layout()

    def _on_size(self, event):
        """
        re-zooms the canvas to fit the window
        """
        self.boardCanvas.ZoomToBB()
        event.Skip()

    def get_canvas(self):
        return self.boardCanvas


class Knight:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Pawn:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class App(wx.App):
    def OnInit(self):
        frame = GameBoard('Knights Game')
        self.SetTopWindow(frame)
        frame.Show()
        return 1


if __name__ == "__main__":
    prog = App(0)
    prog.MainLoop()
