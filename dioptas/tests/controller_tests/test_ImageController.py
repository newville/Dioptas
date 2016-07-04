# -*- coding: utf8 -*-

import os
import gc
import shutil
from tests.utility import QtTest

from PyQt4 import QtCore
from PyQt4.QtTest import QTest

from widgets.integration import IntegrationWidget
from controller.integration.ImageController import ImageController
from model.DioptasModel import DioptasModel

unittest_data_path = os.path.join(os.path.dirname(__file__), '../data')


class ImageControllerTest(QtTest):

    def setUp(self):
        self.working_dir = {'image': ''}

        self.widget = IntegrationWidget()
        self.model = DioptasModel()

        self.controller = ImageController(
            working_dir=self.working_dir,
            widget=self.widget,
            dioptas_model=self.model)

    def tearDown(self):
        if os.path.exists(os.path.join(unittest_data_path, 'image_003.tif')):
            os.remove(os.path.join(unittest_data_path, 'image_003.tif'))
        del self.widget
        del self.model
        del self.controller
        gc.collect()

    def test_automatic_file_processing(self):
        # get into a specific folder
        self.controller.load_file(os.path.join(unittest_data_path, 'image_001.tif'))
        self.assertEqual(str(self.widget.img_filename_txt.text()), 'image_001.tif')
        self.assertEqual(self.controller.working_dir['image'], unittest_data_path)

        # enable autoprocessing:
        QTest.mouseClick(self.widget.autoprocess_cb, QtCore.Qt.LeftButton,
                         pos=QtCore.QPoint(2, self.widget.autoprocess_cb.height() / 2.0))
        self.assertFalse(self.controller._directory_watcher.signalsBlocked())

        self.assertTrue(self.widget.autoprocess_cb.isChecked())
        shutil.copy2(os.path.join(unittest_data_path, 'image_001.tif'),
                     os.path.join(unittest_data_path, 'image_003.tif'))

        self.controller._directory_watcher._file_system_watcher.directoryChanged.emit(unittest_data_path)

        self.assertEqual('image_003.tif', str(self.widget.img_filename_txt.text()))
