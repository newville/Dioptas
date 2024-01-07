# -*- coding: utf-8 -*-
# Dioptas - GUI program for fast processing of 2D X-ray diffraction data
# Principal author: Clemens Prescher (clemens.prescher@gmail.com)
# Copyright (C) 2014-2019 GSECARS, University of Chicago, USA
# Copyright (C) 2015-2018 Institute for Geology and Mineralogy, University of Cologne, Germany
# Copyright (C) 2019-2020 DESY, Hamburg, Germany
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import numpy as np

from dioptas.model import DioptasModel
from dioptas.widgets.MapWidget import MapWidget

from ..widgets.UtilityWidgets import open_files_dialog


class MapController(object):
    def __init__(self, widget: MapWidget, dioptas_model: DioptasModel):
        self.widget = widget
        self.model = dioptas_model

        self.create_signals()

    def create_signals(self):
        self.widget.control_widget.load_btn.clicked.connect(self.load_btn_clicked)
        self.widget.control_widget.file_list.currentRowChanged.connect(
            self.model.map_model.select_point_by_index
        )
        self.widget.map_plot_widget.mouse_left_clicked.connect(self.map_point_selected)
        self.widget.pattern_plot_widget.mouse_left_clicked.connect(self.pattern_clicked)
        self.widget.pattern_plot_widget.map_interactive_roi.sigRegionChanged.connect(
            self.pattern_roi_changed
        )

        self.model.map_model.filenames_changed.connect(self.update_file_list)
        self.model.map_model.map_changed.connect(self.update_map)
        self.model.img_changed.connect(self.update_image)
        self.model.pattern_changed.connect(self.update_pattern)

        self.model.configuration_selected.connect(self.configuration_selected)

    def load_btn_clicked(self):
        filenames = open_files_dialog(
            self.widget,
            "Load image data file(s)",
            self.model.working_directories["image"],
        )
        try:
            self.model.map_model.load(filenames)
            self.model.map_model.select_point(0, 0)
        except ValueError as e:
            self.update_file_list()

    def update_file_list(self):
        self.widget.control_widget.file_list.clear()
        if self.model.map_model.filenames is None:
            return
        self.widget.control_widget.file_list.addItems(self.model.map_model.filenames)
        self.widget.control_widget.file_list.setCurrentRow(0)

    def update_map(self):
        if self.model.map_model.map is None:
            # clear image
            self.widget.map_plot_widget.plot_image(np.array([[], []]))
        else:
            self.widget.map_plot_widget.plot_image(
                np.flipud(self.model.map_model.map), auto_level=True
            )

    def update_image(self):
        if self.model.img_model.img_data is None:
            # clear image
            self.widget.img_plot_widget.plot_image(np.array([[], []]))
        else:
            self.widget.img_plot_widget.plot_image(
                self.model.img_model.img_data, auto_level=True
            )

    def update_pattern(self):
        self.widget.pattern_plot_widget.plot_data(
            self.model.pattern.x, self.model.pattern.y
        )

    def map_point_selected(self, clicked_x, clicked_y):
        clicked_x, clicked_y = np.floor(clicked_x), np.floor(clicked_y)
        row = self.model.map_model.map.shape[0] - int(clicked_y) - 1
        col = int(clicked_x)
        self.model.map_model.select_point(row, col)
        ind = self.model.map_model.get_point_index(row, col)
        self.widget.control_widget.file_list.setCurrentRow(ind)

    def pattern_clicked(self, x, _):
        self.widget.pattern_plot_widget.map_interactive_roi.setCenter(x)

    def pattern_roi_changed(self, interactive_roi):
        region = interactive_roi.getRegion()
        self.model.map_model.set_window(region)

    def configuration_selected(self):
        self.update_file_list()
        self.update_map()
        self.update_image()
        self.update_pattern()
