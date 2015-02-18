# -*- coding: utf8 -*-
__author__ = 'Clemens Prescher'

import numpy as np

def extract_background(x, y, smooth_width=0.1, iterations=50, cheb_order=50):
    """
    Performs a background subtraction using bruckner smoothing and a chebyshev polynomial.
    Standard parameters are found to be optimal for synchrotron XRD.
    :param x: x-data of spectrum
    :param y: y-data of spectrum
    :param smooth_width: width of the window in x-units used for bruckner smoothing
    :param iterations: number of iterations for the bruckner smoothing
    :param cheb_order: order of the fitted chebyshev polynomial
    :return: vector of extracted y background
    """
    smooth_points = int((float(smooth_width)/(x[1]-x[0])))

    y_smooth = smooth_bruckner(x, y, smooth_points, iterations)

    # get cheb input parameters
    x_cheb = 2. * (x - x[0]) / (x[-1] - x[0]) - 1.
    cheb_parameters = np.polynomial.chebyshev.chebfit(x_cheb,
                                                      y_smooth,
                                                      cheb_order)

    return np.polynomial.chebyshev.chebval(x_cheb, cheb_parameters)


def smooth_bruckner(x, y, smooth_points, iterations):
    print smooth_points
    y_original = y

    N_data = y.size
    N = smooth_points
    y = np.empty(N_data + N + N)

    y[N:N + N_data] = y_original[0:N_data]
    y[0:N].fill(y_original[N])
    y[N + N_data:N_data + N + N].fill(y_original[-1])
    y_new = y

    y_avg = np.average(y)
    y_min = np.min(y)

    y_c = y_avg + 2. * (y_avg - y_min)

    y[y > y_c] = y_c

    for j in range(0, iterations):
        for i in range(N, N_data - 1 - N - 1):
            y_new[i] = np.min([y[i], np.average(y[i - N:i + N + 1])])
            y = y_new

    return y[N:N + N_data]