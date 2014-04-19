__author__ = 'Clemens Prescher'

import pyqtgraph as pg
import numpy as np
from PyQt4 import QtCore, QtGui


class SpectrumView(object):
    def __init__(self, pg_layout):
        self.pg_layout = pg_layout

        self.create_graphics()
        self.create_line_plot()
        self.modify_mouse_behavior()
        self.phases = []

        self.mouse_move_observer = []
        self.left_click_observer = []

        self.plot_vertical_lines([2, 54, 7, 8])

    def add_left_click_observer(self, function):
        self.left_click_observer.append(function)

    def add_mouse_move_observer(self, function):
        self.mouse_move_observer.append(function)

    def create_graphics(self):
        self.spectrum_plot = self.pg_layout.addPlot(labels = {'left': 'Intensity','bottom':'2 Theta'})
        self.img_view_box = self.spectrum_plot.vb

    def create_line_plot(self):
        self.plot_item = pg.PlotDataItem(np.linspace(0, 10), np.sin(np.linspace(10, 3)),
                                         pen = pg.mkPen(color=(255,125,0), width=1.5))
        self.spectrum_plot.addItem(self.plot_item)

    def plot_data(self, x, y):
        self.plot_item.setData(x, y)

    def plot_vertical_lines(self, positions, phase_index=0, name = None):
        if len(self.phases)<=phase_index:
            self.phases.append( PhaseLinesPlot(self.spectrum_plot,  positions))
            self.add_left_click_observer(self.phases[phase_index].onMouseClick)
        else:
            self.phases[phase_index].set_data(positions, name)

    def mouseMoved(self, pos):
        pos = self.plot_item.mapFromScene(pos)
        for function in self.mouse_move_observer:
            function(pos.x(), pos.y())


    def modify_mouse_behavior(self):
        #different mouse handlers
        self.img_view_box.setMouseMode(self.img_view_box.RectMode)

        self.pg_layout.scene().sigMouseMoved.connect(self.mouseMoved)
        self.img_view_box.mouseClickEvent = self.myMouseClickEvent
        self.img_view_box.mouseDragEvent = self.myMouseDragEvent
        self.img_view_box.mouseDoubleClickEvent = self.myMouseDoubleClickEvent
        self.img_view_box.wheelEvent = self.myWheelEvent


    def myMouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            view_range = np.array(self.img_view_box.viewRange()) * 2
            curve_data=self.plot_item.getData()
            x_range=np.max(curve_data[0])-np.min(curve_data[0])
            y_range=np.max(curve_data[1])-np.min(curve_data[1])
            if (view_range[0][1] - view_range[0][0]) > x_range and \
                            (view_range[1][1] - view_range[1][0]) > y_range:
                self.img_view_box.autoRange()
            else:
                self.img_view_box.scaleBy(2)
        if ev.button() == QtCore.Qt.LeftButton:
            pos = self.img_view_box.mapFromScene(ev.pos())
            pos = self.plot_item.mapFromScene(2 * ev.pos() - pos)
            x = pos.x()
            y = pos.y()
            for function in self.left_click_observer:
                function(x, y)


    def myMouseDoubleClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.img_view_box.autoRange()


    def myMouseDragEvent(self, ev, axis=None):
        #most of this code is copied behavior of left click mouse drag from the original code
        ev.accept()
        pos = ev.pos()
        lastPos = ev.lastPos()
        dif = pos - lastPos
        dif = dif * -1
        ## Ignore axes if mouse is disabled
        mouseEnabled = np.array(self.img_view_box.state['mouseEnabled'], dtype=np.float)
        mask = mouseEnabled.copy()
        if axis is not None:
            mask[1 - axis] = 0.0

        if ev.button() == QtCore.Qt.RightButton:
            #determine the amount of translation
            tr = dif * mask
            tr = self.img_view_box.mapToView(tr) - self.img_view_box.mapToView(pg.Point(0, 0))
            x = tr.x()
            y = tr.y()

            self.img_view_box.translateBy(x=x, y=y)
            self.img_view_box.sigRangeChangedManually.emit(self.img_view_box.state['mouseEnabled'])
        else:
            pg.ViewBox.mouseDragEvent(self.img_view_box, ev)


    def myWheelEvent(self, ev):
        if ev.delta() > 0:
            pg.ViewBox.wheelEvent(self.img_view_box, ev)
        else:
            view_range = np.array(self.img_view_box.viewRange())
            curve_data=self.plot_item.getData()
            x_range=np.max(curve_data[0])-np.min(curve_data[0])
            y_range=np.max(curve_data[1])-np.min(curve_data[1])
            if (view_range[0][1] - view_range[0][0]) > x_range and \
                            (view_range[1][1] - view_range[1][0]) > y_range:
                self.img_view_box.autoRange()
            else:
                pg.ViewBox.wheelEvent(self.img_view_box, ev)


class PhaseLinesPlot(object):
    def __init__(self, plot_item, positions = None, name = 'HAHAHA', pen = pg.mkPen(color=(120,120,120), style=QtCore.Qt.DashLine) ):
        self.plot_item=plot_item
        self.peak_positions = []
        self.line_items = []
        self.pen=pen
        self.name=name
        self.label = pg.TextItem(text=name, anchor=(1,1))

        self.search_range=0.1

        if positions is not None:
            self.set_data(positions, name)

    def set_data(self, positions, name):
        #remove all old lines
        for item in self.line_items:
            self.plot_item.removeItem(item)

        #create new ones on each Position:
        self.line_items = []
        self.peak_positions = positions
        for ind, position in enumerate(positions):
            self.line_items.append(pg.InfiniteLine(pen = self.pen))
            self.line_items[ind].setValue(position)
            self.plot_item.addItem(self.line_items[ind])

        if name is not None:
            self.plot_item.removeItem(self.label)
            self.label = pg.TextItem(text=name, anchor=(1,1), color=self.pen.color())
            self.plot_item.addItem(self.label)
            self.label.hide()

    def onMouseClick(self, x,y):
        if self.atLine(x):
            self.label.setPos(x,y)
            self.label.show()
        else:
            self.label.hide()

    def atLine(self, x):
        for position in self.peak_positions:
            if x>(position-self.search_range)\
                and x < (position+self.search_range):
                return True
        return False











