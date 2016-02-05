# The following file contains an open-source, non-Matlab HOG visualizer.
#
# Copyright (C) 2016 Boone Adkins
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import matplotlib.pyplot as plt
import numpy as np

def inria_hog_reshape(hog, win_size, block_size, block_stride, cell_size, nbins):
    '''
    Reshapes a 1D Histogram of Oriented Gradients to a 4D array.
    :param hog: A HOG descriptor following the INRIA standard. (E.g. from
    OpenCV.) Shape must be (x, y, cell, bin)
    :param win_size: Window size two-tuple, (x, y).
    :param block_size: Block size two-tuple, (x, y)
    :param block_stride: How far each successive block is shifted. Two-tuple,
    (x, y).
    :param cell_size: Cell size two-tuple, (x, y).
    :param nbins: Number of angle bins.
    :return: Hog with shape (x, y, cell, bin)
    '''
    new_shape = [win_size[1]/block_stride[1] - 1, win_size[0]/block_stride[0] - 1,
                 block_size[0]/cell_size[0]*block_size[1]/cell_size[1], nbins]
    hog.shape = new_shape
    return hog

def plot_hog_grid(win_size, cellSize, color='g'):
    plt.vlines(np.arange(0, win_size[0], cellSize[0]), 0, win_size[1], color=color)
    plt.hlines(np.arange(0, win_size[1], cellSize[1]), 0, win_size[0], color=color)

def plot_hog(hog, win_size, cell_size, n_bins, combine_bins=True, color='r', **kwargs):
    '''
    Visualizes a Histogram of Oriented Gradients using glyphs.
    :param hog: A HOG descriptor. Shape must be (x, y, cell, bin)
    :param win_size: Window size two-tuple, (x, y).
    :param cell_size: Cell size two-tuple, (x, y).
    :param n_bins: Number of angle bins.
    :param combine_bins: True to display the vector sum of the angle bins
    False to display a line for each one.
    :param color: Any acceptable Matplotlib color.
    :param kwargs: Will be passed directly to pyplot.quiver().
    :return:
    '''

    # Default plot settings
    kwargs_ = {'scale': cell_size[0], 'width': 0.01, 'headwidth': 1e-9, 'angles': 'xy', 'minshaft': 1, 'pivot': 'mid',
               'headlength': 1e-9, 'headaxislength': 1e-9}
    kwargs_.update(kwargs)  # Overwrites existing settings

    hog = np.swapaxes(hog, 0, 1)  # Swaps x, y to y, x

    x = np.arange(cell_size[0]/2, win_size[0] - cell_size[0], cell_size[0])
    y = np.arange(cell_size[1]/2, win_size[1] - cell_size[1], cell_size[1])
    X, Y = np.meshgrid(x, y)

    angles = np.arange(0, np.pi, np.pi/n_bins)
    u = hog[:, :, 0, :] * np.cos(angles)
    v = hog[:, :, 0, :] * np.sin(angles)

    n_bins = 9  # Number of bins
    if combine_bins:
        U = np.sum(u, axis=2)
        V = np.sum(v, axis=2)
        lengths = np.sqrt(U**2 + V**2)
        U /= np.max(lengths)
        V /= np.max(lengths)

        plt.quiver(X, Y, U, V, color=color, **kwargs_)
    else:
        # Plot each HOG angle
        for b in range(0, n_bins):  # The HOG angles bins
            U = u[:, :, b]
            V = v[:, :, b]
            lengths = np.sqrt(U**2 + V**2)
            U /= np.max(lengths)
            V /= np.max(lengths)

            plt.quiver(X, Y, U, V, color=color, **kwargs_)
