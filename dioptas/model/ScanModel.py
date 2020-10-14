import logging
import os

import h5py
import numpy as np
from qtpy import QtCore

from .util import extract_background

logger = logging.getLogger(__name__)


class ScanModel(QtCore.QObject):
    """
    Class describe a model for batch integration
    """

    def __init__(self, calibration_model, mask_model):
        super(ScanModel, self).__init__()

        self.data = None
        self.binning = None

        self.file_map = None
        self.files = None
        self.pos_map = None
        self.n_img = None

        self.calibration_model = calibration_model
        self.mask_model = mask_model

    def set_image_files(self, files):
        """
        Set internal variables with respect of given list of files.

        Open each file and count number of images inside. Position of each image in the file
        and total number of images are stored in internal variables.

        :param files: List of file names including path
        """
        pos_map = []
        file_map = []
        image_counter = 0
        for file in files:
            self.calibration_model.img_model.load(file)
            file_map.append(image_counter)
            image_counter += self.calibration_model.img_model.series_max
            pos_map += list(range(self.calibration_model.img_model.series_max))

        self.pos_map = np.array(pos_map)
        self.files = np.array(files)
        self.file_map = np.array(file_map)
        self.n_img = image_counter

    def load_proc_data(self, filename):
        """
        Load diffraction patterns and metadata from h5 file

        """
        with h5py.File(filename, "r") as data_file:
            self.data = data_file['data'][()]
            self.binning = data_file['binning'][()]
            self.file_map = data_file['file_map'][()]
            self.files = data_file['files'][()].astype('U')
            self.pos_map = data_file['pos_map'][()]
            self.n_img = self.data.shape[0]

            cal_file = str(data_file.attrs['calibration'])
            self.calibration_model.load(cal_file)
            if 'mask' in data_file.attrs:
                mask_file = data_file.attrs['mask']
                self.mask_model.load_mask(mask_file)

    def save_proc_data(self, filename):
        """
        Save diffraction patterns to h5 file
        """
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with h5py.File(filename, mode="w") as f:
            f.attrs['calibration'] = self.calibration_model.filename
            f.attrs['int_method'] = 'Bla'
            f.attrs['num_points'] = self.binning.shape[0]
            # ToDo Save mask if applied

            f.create_dataset("data", data=self.data)
            f.create_dataset("binning", data=self.binning)
            f.create_dataset("pos_map", data=self.pos_map)
            f.create_dataset("file_map", data=self.file_map)
            f.create_dataset("files", data=self.files.astype('S'))

    def save_as_csv(self, filename):
        """
        Save diffraction patterns to 3-columns csv file
        """
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        x = self.binning.repeat(self.n_img)
        y = np.arange(self.n_img)[None,:].repeat(self.binning.shape[0], axis=0).flatten()
        np.savetxt(filename, np.array(list(zip(x, y, self.data.T.flatten()))), delimiter=',', fmt='%f')

    def integrate_raw_data(self, progress_dialog, num_points):
        """
        Integrate images from given file

        :param progress_dialog: Progress dialog to show progress
        :param num_points: Numbers of radial bins
        """
        data = []
        image_counter = 0
        if self.mask_model.mode:
            mask = self.mask_model.get_mask()
        for file in self.files:
            self.calibration_model.img_model.load(file)

            for i in range(self.calibration_model.img_model.series_max):
                if progress_dialog.wasCanceled():
                    break
                image_counter += 1
                progress_dialog.setValue(image_counter)
                self.calibration_model.img_model.load_series_img(i)
                binning, intensity = self.calibration_model.integrate_1d(num_points=num_points,
                                                                         mask=mask)
                data.append(intensity)

        self.binning = np.array(binning)
        self.data = np.array(data)

    def subtract_background(self, parameters, progress_dialog):
        """
        Subtract background calculated with respect of given parameters
        """

        data_bkg = np.zeros(self.data.shape)
        for i, y in enumerate(self.data):
            if progress_dialog.wasCanceled():
                break

            progress_dialog.setValue(i)
            data_bkg[i] = extract_background(self.binning, y,
                                           parameters[0],
                                           parameters[1],
                                           parameters[2])
        return self.data-data_bkg

    def get_image_info(self, index):
        """
        Get filename and image position in the file

        :param index: Index of image in the batch
        """
        f_index = np.where(self.file_map <= index)[0][-1]
        filename = self.files[f_index]
        pos = self.pos_map[index]
        return filename, pos

    def load_image(self, index):
        """
        Load image in image model

        :param index: Index of image in the batch
        """
        filename, pos = self.get_image_info(index)
        self.calibration_model.img_model.load(filename, pos)
