#!/usr/bin/python
#try

from PyQt4 import QtGui, QtCore, uic
from scipy import optimize
import sys
import numpy as np
from acc_ctl.service_daemon import Service

import pycx4.qcda as cda

class DissApp(object):
    def __init__(self, adcname, devname):
        super(DissApp, self).__init__()

        self.init_chans(adcname, devname)

        self.measured_area_size = 20000
        self.number_thinned = 10
        self.delay = 17000

        self.CALIBRATE = 5.45 / 10000 * self.number_thinned * 1

        self.chan_data.valueMeasured.connect(self.data_processing)

    def init_chans(self, adcname, devname):
        self.chan_data = cda.VChan(adcname, max_nelems=65535)
        self.chan_thinned_data = cda.VChan(devname + ".resample_data", max_nelems=65535)
        self.chan_fit_data = cda.VChan(devname + ".fit_data", max_nelems=65535)
        self.chan_sigma = cda.DChan(devname + ".fit_sigma")
        self.chan_amplitude = cda.DChan(devname + ".fit_a")
        self.chan_t0 = cda.DChan(devname + ".fit_t0")
        self.chan_time_fit_data = cda.VChan(devname + ".time_fit_data", max_nelems=65535)

    def data_processing(self):
        y_fit_data = self.thin_data(self.chan_data.val[self.delay:(self.delay+self.measured_area_size)])
        x_fit_data = np.arange(0, y_fit_data.__len__(), 1, dtype=np.float64)

        self.fit(x_fit_data, y_fit_data)

    def thin_data(self, measured_y_data):
        sum = 0
        new_size = int(round(self.measured_area_size / self.number_thinned))
        y_thinned = np.zeros((new_size,))
        for j in range(0, new_size):
            for i in range(self.number_thinned * (j - 1), self.number_thinned * j):
                sum += measured_y_data[i]
            y_thinned[j] = sum / self.number_thinned * 1000  #V->mV
            sum = 0
        self.chan_thinned_data.setValue(y_thinned)
        return y_thinned

    def fit(self, x_data, y_data):
        if y_data.max() > 30:
            gaussfit = lambda p, x: p[0] * np.exp(-(((x - p[1]) / p[2]) ** 2) / 2) + p[3]
            errfunc = lambda p, x, y: gaussfit(p, x) - y_data
            p = [0.07, y_data.argmax(), 100, 0]
            p1, success = optimize.leastsq(errfunc, p[:], args=(x_data, y_data))

            self.chan_fit_data.setValue(gaussfit(p1, x_data))
            self.chan_time_fit_data.setValue(x_data * self.CALIBRATE)

            p1[1] *= self.CALIBRATE
            p1[2] *= self.CALIBRATE
            print p1[2], p1[1], y_data.argmax() * self.CALIBRATE, p1[0], y_data.max()
            self.chan_amplitude.setValue(p1[0])
            self.chan_t0.setValue(p1[1])
            self.chan_sigma.setValue(abs(p1[2]))


def main_proc():
    import cothread

    a = QtCore.QCoreApplication(sys.argv)
    app = cothread.iqt()
    w = DissApp("cxhw:18.bal333_2.line3", 'cxhw:0.e_diss')
    cothread.WaitForQuit()


def clear_proc():
    pass

a = Service('dissector', main_proc, clear_proc)