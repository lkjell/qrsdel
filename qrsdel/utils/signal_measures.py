# -*- coding: utf-8 -*-
# pylint: disable-msg=E1101
"""
Created on Mon Jun  4 10:53:10 2012

This module contains the definition of several utility functions to perform
measurements over signals.

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 3.0 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library.

@author: T. Teijeiro
"""

import scipy.stats
import numpy as np
from .constants import CONSTANTS as C
from ..signal_buffer import get_signal_fragment


def mode(signal):
    """Obtains the mode of a signal fragment"""
    nbins = int((signal.max() - signal.min()) / C.BL_MARGIN) or 1
    hist = np.histogram(signal, nbins)
    peak = hist[0].argmax()
    return hist[1][peak] + (hist[1][peak + 1] - hist[1][peak]) / 2.0


def kurtosis(signal):
    """
    Obtains the kurtosis of a signal fragment. We use this value as an
    indicator of the signal quality.
    """
    return scipy.stats.kurtosis(signal)


def mvkurtosis(arr):
    """
    Obtains the kurtosis of a multivariate array of data. The first dimension
    of *arr* contains the variables, and the second the values.
    """
    n = np.size(arr, 1)
    # Mean vector and corrected covariance matrix
    med = np.mean(arr, 1)
    s = np.cov(arr) * (n - 1) / n
    # Eigenvalue and eigenvector calculation
    lamb, v = np.linalg.eig(s)
    si12 = np.dot(np.dot(v, np.diag(1.0 / np.sqrt(lamb))), np.transpose(v))
    # Multivariant standardization
    medrep = np.transpose(np.repeat(np.asmatrix(med), n, 0))
    xs = np.dot(np.transpose(arr - medrep), si12)
    # Similarities
    r = np.dot(xs, np.transpose(xs))
    return np.sum(np.diag(r) ** 2) / n


def mvskewness(arr):
    """
    Obtains the skewness of a multivariate array of data. The first dimension
    of *arr* contains the variables, and the second the values.
    """
    n = np.size(arr, 1)
    # Mean vector and corrected covariance matrix
    med = np.mean(arr, 1)
    s = np.cov(arr) * (n - 1) / n
    # Eigenvalue and eigenvector calculation
    lamb, v = np.linalg.eig(s)
    si12 = np.dot(np.dot(v, np.diag(1.0 / np.sqrt(lamb))), np.transpose(v))
    # Multivariant standardization
    medrep = np.transpose(np.repeat(np.asmatrix(med), n, 0))
    xs = np.dot(np.transpose(arr - medrep), si12)
    # Similarities
    r = np.array(np.dot(xs, np.transpose(xs)))
    return np.sum(r ** 3) / (n * n)


def get_peaks(arr):
    """
    Obtains the indices in an array where a peak is present, this is, where
    a change in the sign of the first derivative is found. The points with
    zero derivative are associated to the current trend.

    Parameters
    ----------
    arr:
        NumPy array

    Returns
    -------
    out:
        NumPy array containing the indices where there are peaks.
    """
    if len(arr) < 3:
        raise ValueError("The array needs to have at least three values")
    sdif = np.sign(np.diff(arr))
    # If all the series has zero derivative, there are no peaks.
    if not np.any(sdif):
        return np.array([])
    # If the sequence starts with a zero derivative, we associate it to the
    # first posterior trend.
    if sdif[0] == 0:
        i = 1
        while sdif[i] == 0:
            i += 1
        sdif[0] = sdif[i]
    for i in range(1, len(sdif)):
        if sdif[i] == 0:
            sdif[i] = sdif[i - 1]
    return np.where(sdif[1:] != sdif[:-1])[0] + 1


def characterize_baseline(lead, beg, end):
    """
    Obtains the baseline estimation for a fragment delimited by two time
    points in a specific lead. It also obtains a quality estimator for the
    fragment.

    Parameters
    ----------
    lead:
        Selected lead to obtain the baseline estimator.
    beg:
        Starting sample of the interval.
    end:
        Ending sample of the interval.

    Returns
    ------
    out: (baseline, quality)
        Tuple with (baseline, quality) estimators. At the moment, the quality
        estimator is not yet numerically characterized, but we have strong
        evidence that the higher this value is, the higher the signal quality
        of the fragment where the baseline has been estimated.
    """
    assert beg >= 0 and end >= beg
    # We need at least 1 second of signal to estimate the baseline and the
    # quality.
    if end - beg < C.BL_MIN_LEN:
        center = beg + (end - beg) / 2.0
        beg = max(0, int(center - C.BL_MIN_LEN / 2))
        end = int(center + C.BL_MIN_LEN / 2)
    signal = get_signal_fragment(beg, end, lead=lead)[0]
    return (mode(signal), kurtosis(signal))
