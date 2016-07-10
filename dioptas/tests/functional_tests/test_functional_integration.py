# -*- coding: utf8 -*-
import gc
import os
import unittest

import numpy as np

from PyQt4 import QtGui, QtCore
from PyQt4.QtTest import QTest

from mock import MagicMock

from model.DioptasModel import DioptasModel
from widgets.integration import IntegrationWidget
from controller.integration import IntegrationController

unittest_path = os.path.dirname(__file__)
data_path = os.path.join(unittest_path, os.pardir, 'data')


def click_button(widget):
    QTest.mouseClick(widget, QtCore.Qt.LeftButton)


class IntegrationMockFunctionalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtGui.QApplication.instance()
        if cls.app is None:
            cls.app = QtGui.QApplication([])

    def setUp(self):
        self.model = DioptasModel()
        self.model.calibration_model.integrate_1d = MagicMock(return_value=(self.model.calibration_model.tth,
                                                                            self.model.calibration_model.int))

        self.integration_widget = IntegrationWidget()
        self.integration_controller = IntegrationController({'spectrum': data_path},
                                                            widget=self.integration_widget,
                                                            dioptas_model=self.model)
        self.model.calibration_model.load(os.path.join(data_path, 'CeO2_Pilatus1M.poni'))
        self.model.img_model.load(os.path.join(data_path, 'CeO2_Pilatus1M.tif'))

        self.integration_spectrum_controller = self.integration_controller.spectrum_controller
        self.integration_image_controller = self.integration_controller.image_controller

    def tearDown(self):
        del self.integration_spectrum_controller
        del self.integration_controller
        self.model.clear()
        del self.model
        gc.collect()

    def enter_value_into_text_field(self, text_field, value):
        text_field.setText('')
        QTest.keyClicks(text_field, str(value))
        QTest.keyPress(text_field, QtCore.Qt.Key_Enter)
        QtGui.QApplication.processEvents()

    def test_changing_number_of_integration_bins(self):
        # Edith wants to change the number of integration bins in order to see the effect of binning onto her line
        # shape. She sees that there is an option in the X tab and deselects automatic and sees that the sbinbox
        # becomes editable.
        self.assertFalse(self.integration_widget.bin_count_txt.isEnabled())
        self.integration_widget.automatic_binning_cb.setChecked(False)
        self.assertTrue(self.integration_widget.bin_count_txt.isEnabled())

        # she sees that the current value and wants to double it and notices that the spectrum looks a little bit
        # smoother
        previous_number_of_points = len(self.model.pattern_model.pattern.x)
        self.enter_value_into_text_field(self.integration_widget.bin_count_txt, 2 * previous_number_of_points)

        self.model.calibration_model.integrate_1d.assert_called_with(num_points=2 * previous_number_of_points,
                                                                     mask=None, unit='2th_deg')

        # then she decides that having an automatic estimation may probably be better and changes back to automatic.
        # immediately the number is restored and the image looks like when she started
        self.integration_widget.automatic_binning_cb.setChecked(True)
        self.model.calibration_model.integrate_1d.assert_called_with(num_points=None,
                                                                     mask=None, unit='2th_deg')

    def test_changing_supersampling_amount_integrating_to_cake_with_mask(self):
        # Edith opens the program, calibrates everything and looks in to the options menu. She sees that there is a
        # miraculous parameter called supersampling. It is currently set to 1 which seems to be normal
        self.assertEqual(self.integration_widget.supersampling_sb.value(), 1)

        # then she sets it to two and she sees that the number of spectrum bin changes and that the spectrum looks
        # smoother

        # values before:
        px1 = self.model.calibration_model.spectrum_geometry.pixel1
        px2 = self.model.calibration_model.spectrum_geometry.pixel2

        img_shape = self.model.img_model.img_data.shape

        self.integration_widget.supersampling_sb.setValue(2)
        self.assertEqual(self.model.calibration_model.spectrum_geometry.pixel1, 0.5 * px1)
        self.assertEqual(self.model.calibration_model.spectrum_geometry.pixel2, 0.5 * px2)
        self.assertEqual(self.model.calibration_model.cake_geometry.pixel1, px1)
        self.assertEqual(self.model.calibration_model.cake_geometry.pixel2, px2)

        self.assertEqual(self.model.img_model.img_data.shape[0], 2 * img_shape[0])
        self.assertEqual(self.model.img_model.img_data.shape[1], 2 * img_shape[1])

        self.model.mask_model.load_mask(os.path.join(data_path, 'test.mask'))
        QTest.mouseClick(self.integration_widget.img_mask_btn, QtCore.Qt.LeftButton)
        QTest.mouseClick(self.integration_widget.img_mode_btn, QtCore.Qt.LeftButton)

    def test_saving_image(self):
        # the widget has to be shown to be able to save the image:
        self.integration_widget.show()
        # Tests if the image save procedures are working for the different possible file endings
        self.integration_image_controller.save_img(os.path.join(data_path, 'Test_img.png'))
        self.integration_image_controller.save_img(os.path.join(data_path, 'Test_img.tiff'))

        self.assertTrue(os.path.exists(os.path.join(data_path, 'Test_img.png')))
        self.assertTrue(os.path.exists(os.path.join(data_path, 'Test_img.tiff')))

        os.remove(os.path.join(data_path, 'Test_img.png'))
        os.remove(os.path.join(data_path, 'Test_img.tiff'))

    def test_saving_spectrum(self):
        # the widget has to be shown to be able to save the image:
        self.integration_widget.show()

        # Tests if the spectrum save procedures is are working for all fileendings
        def save_spectra_test_for_size_and_delete(self):
            self.integration_spectrum_controller.save_pattern(os.path.join(data_path, 'Test_spec.xy'))
            self.integration_spectrum_controller.save_pattern(os.path.join(data_path, 'Test_spec.chi'))
            self.integration_spectrum_controller.save_pattern(os.path.join(data_path, 'Test_spec.dat'))
            self.integration_spectrum_controller.save_pattern(os.path.join(data_path, 'Test_spec.png'))
            self.integration_spectrum_controller.save_pattern(os.path.join(data_path, 'Test_spec.svg'))

            self.assertTrue(os.path.exists(os.path.join(data_path, 'Test_spec.xy')))
            self.assertTrue(os.path.exists(os.path.join(data_path, 'Test_spec.chi')))
            self.assertTrue(os.path.exists(os.path.join(data_path, 'Test_spec.dat')))
            self.assertTrue(os.path.exists(os.path.join(data_path, 'Test_spec.png')))
            self.assertTrue(os.path.exists(os.path.join(data_path, 'Test_spec.svg')))

            self.assertGreater(os.stat(os.path.join(data_path, 'Test_spec.xy')).st_size, 1)
            self.assertGreater(os.stat(os.path.join(data_path, 'Test_spec.chi')).st_size, 1)
            self.assertGreater(os.stat(os.path.join(data_path, 'Test_spec.dat')).st_size, 1)
            self.assertGreater(os.stat(os.path.join(data_path, 'Test_spec.png')).st_size, 1)
            self.assertGreater(os.stat(os.path.join(data_path, 'Test_spec.svg')).st_size, 1)

            os.remove(os.path.join(data_path, 'Test_spec.xy'))
            os.remove(os.path.join(data_path, 'Test_spec.chi'))
            os.remove(os.path.join(data_path, 'Test_spec.dat'))
            os.remove(os.path.join(data_path, 'Test_spec.png'))
            os.remove(os.path.join(data_path, 'Test_spec.svg'))

        save_spectra_test_for_size_and_delete(self)
        QTest.mouseClick(self.integration_spectrum_controller.widget.spec_q_btn, QtCore.Qt.LeftButton)
        save_spectra_test_for_size_and_delete(self)
        QTest.mouseClick(self.integration_spectrum_controller.widget.spec_d_btn, QtCore.Qt.LeftButton)
        save_spectra_test_for_size_and_delete(self)

    def test_undocking_and_docking_img_frame(self):
        QTest.mouseClick(self.integration_widget.img_dock_btn, QtCore.Qt.LeftButton)
        QTest.mouseClick(self.integration_widget.img_dock_btn, QtCore.Qt.LeftButton)

    def test_loading_multiple_images_and_batch_integrate_them(self):
        self.integration_widget.spec_autocreate_cb.setChecked(True)
        self.assertTrue(self.integration_widget.spec_autocreate_cb.isChecked())
        self.integration_image_controller.load_file([os.path.join(data_path, 'image_001.tif'),
                                                     os.path.join(data_path, 'image_002.tif')])
        self.assertTrue(os.path.exists(os.path.join(data_path, 'image_001.xy')))
        self.assertTrue(os.path.exists(os.path.join(data_path, 'image_002.xy')))
        os.remove(os.path.join(data_path, 'image_001.xy'))
        os.remove(os.path.join(data_path, 'image_002.xy'))


class IntegrationFunctionalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtGui.QApplication.instance()
        if cls.app is None:
            cls.app = QtGui.QApplication([])

    def setUp(self):
        self.model = DioptasModel()

        self.integration_widget = IntegrationWidget()
        self.integration_controller = IntegrationController({'spectrum': data_path},
                                                            widget=self.integration_widget,
                                                            dioptas_model=self.model)
        self.model.calibration_model.load(os.path.join(data_path, 'CeO2_Pilatus1M.poni'))
        self.model.img_model.load(os.path.join(data_path, 'CeO2_Pilatus1M.tif'))

        self.integration_spectrum_controller = self.integration_controller.spectrum_controller
        self.integration_image_controller = self.integration_controller.image_controller

    def test_activating_mask_mode(self):
        y1 = self.model.pattern_model.pattern.y

        self.model.mask_model.mask_below_threshold(self.model.img_model.img_data, 1)
        click_button(self.integration_widget.img_mask_btn)
        y2 = self.model.pattern_model.pattern.y
        self.assertFalse(np.array_equal(y1, y2))

        click_button(self.integration_widget.img_mask_btn)
        y3 = self.model.pattern_model.pattern.y
        self.assertTrue(np.array_equal(y1, y3))

    def test_activating_roi_mode(self):
        y1 = self.model.pattern_model.pattern.y

        click_button(self.integration_widget.img_roi_btn)
        self.assertIsNotNone(self.model.current_configuration.mask_model.roi_mask)

        y2 = self.model.pattern_model.pattern.y
        self.assertFalse(np.array_equal(y1, y2))

        click_button(self.integration_widget.img_roi_btn)
        y3 = self.model.pattern_model.pattern.y
        self.assertTrue(np.array_equal(y1, y3))

    def test_activating_roi_mode_and_mask_mode(self):
        y1 = self.model.pattern_model.pattern.y

        self.model.mask_model.mask_below_threshold(self.model.img_model.img_data, 1)
        click_button(self.integration_widget.img_mask_btn)
        y2 = self.model.pattern_model.pattern.y

        click_button(self.integration_widget.img_roi_btn)
        y3 = self.model.pattern_model.pattern.y

        click_button(self.integration_widget.img_roi_btn)
        y4 = self.model.pattern_model.pattern.y

        click_button(self.integration_widget.img_mask_btn)
        y5 = self.model.pattern_model.pattern.y

        self.assertFalse(np.array_equal(y3, y1))
        self.assertFalse(np.array_equal(y3, y2))
        self.assertFalse(np.array_equal(y3, y4))

        self.assertFalse(np.array_equal(y1, y2))
        self.assertFalse(np.array_equal(y1, y4))
        self.assertFalse(np.array_equal(y1, y3))
        self.assertTrue(np.array_equal(y1, y5))

    def test_moving_roi(self):
        click_button(self.integration_widget.img_roi_btn)
        roi_limits1 = self.integration_widget.img_widget.roi.getRoiLimits()
        y1 = self.model.pattern_model.pattern.y
        self.integration_widget.img_widget.roi.setX(30)
        self.integration_widget.img_widget.roi.setPos((31, 31))
        self.integration_widget.img_widget.roi.setSize((100, 100))
        roi_limits2 = self.integration_widget.img_widget.roi.getRoiLimits()
        y2 = self.model.pattern_model.pattern.y

        self.assertNotEqual(roi_limits1, roi_limits2)
        self.assertFalse(np.array_equal(y1, y2))