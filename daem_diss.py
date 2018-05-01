#!/usr/bin/python

from PyQt4 import QtCore
from scipy import optimize, integrate
import sys
import numpy as np
import math as mh
from acc_ctl.service_daemon import Service

import pycx4.qcda as cda


class DissApp(object):
    def __init__(self, adcname, devname):
        super(DissApp, self).__init__()

        self.init_chans(adcname, devname)

        self.measured_area_size = 21500
        self.number_thinned = 10
        self.delay = 18500
        self.FIT_CHOOSE = 'gauss'
        self.CALIBRATE = 4.8518 / 10000 * self.number_thinned

        self.x_fit_data = np.arange(0, self.measured_area_size/self.number_thinned, 1, dtype=np.float64)
        self.x_fit_data -= self.x_fit_data[int(self.measured_area_size/self.number_thinned/2)]
        self.x_fit_data *= self.CALIBRATE

    def init_chans(self, adcname, devname):
        self.chan_data = cda.VChan(adcname, max_nelems=65535)
        self.chan_thinned_data = cda.VChan(devname + ".resample_data", max_nelems=65535)
        self.chan_fit_data = cda.VChan(devname + ".fit_data", max_nelems=65535)
        self.chan_sigma = cda.DChan(devname + ".fit_sigma")
        self.chan_amplitude = cda.DChan(devname + ".fit_a")
        self.chan_t0 = cda.DChan(devname + ".fit_t0")
        self.chan_time_fit_data = cda.VChan(devname + ".time_fit_data", max_nelems=65535)

        self.chan_data.valueMeasured.connect(self.data_processing)

        # for fit ctrl
        self.chan_err_mess = cda.StrChan("cxhw:2.e_diss" + ".err_mess", on_update=1, max_nelems=1024)
        self.chan_fit_switch = cda.StrChan("cxhw:2.e_diss" + ".fit_switch", on_update=1, max_nelems=1024)
        self.chan_make_model_fit = cda.DChan("cxhw:2.e_diss" + ".make_model_fit", on_update=1)

        self.chan_fit_switch.valueChanged.connect(self.fit_switch)

    def data_processing(self):
        y_thinned = self.thin_data(self.chan_data.val[self.delay:(self.delay+self.measured_area_size)])

        fit_param, y_fit_data, x_fit_data = self.fit(self.x_fit_data, y_thinned)
        self.chan_thinned_data.setValue(y_thinned)
        self.chan_fit_data.setValue(y_fit_data)
        self.chan_time_fit_data.setValue(x_fit_data)
        self.chan_t0.setValue(fit_param[1])
        self.chan_sigma.setValue(abs(fit_param[2]))

    def thin_data(self, measured_y_data):
        sum = 0
        new_size = int(round(self.measured_area_size / self.number_thinned))
        y_thinned = np.zeros((new_size,))
        for j in range(0, new_size):
            for i in range(self.number_thinned * (j - 1), self.number_thinned * j):
                sum += measured_y_data[i]
            y_thinned[j] = sum / self.number_thinned * 1000  # V ---> mV
            sum = 0
        return y_thinned

    def fit(self, x_data, y_data):
        if y_data.max() > 30:
            if self.FIT_CHOOSE == 'gauss':
                gaussfit = lambda p, x: p[0] * np.exp(-(((x - p[1]) / p[2]) ** 2) / 2) + p[3]
                errfunc = lambda p, x, y: gaussfit(p, x) - y_data
                p = [0.07, (y_data.argmax()-1075) * self.CALIBRATE, 0.6, 0]
                p1, pcov, infodict, errmsg, success = optimize.leastsq(errfunc, p[:], args=(x_data, y_data),
                                                                       full_output=1, epsfcn=0.0001)
                # s_sq = (errfunc(p1, x_data, y_data)**2).sum()/(y_data.__len__() - p.__len__())
                # errfit = []
                # for i in range(p1.__len__()):
                #     errfit.append(np.absolute(pcov[i][i]**0.5 * s_sq))
                return p1, gaussfit(p1, x_data), x_data
            elif self.FIT_CHOOSE == 'model':
                if self.chan_make_model_fit.val:
                    try:
                        modelfit = lambda p, x: p[3] + (mh.sqrt(2/mh.pi)/p[0]) * p[4] * np.exp(-(((x - p[1]) / p[2]) ** 2) / 2) / \
                                                       (mh.cosh(p[0]/2)/mh.sinh(p[0]/2) - self.erf((x - p[1]) / mh.sqrt(2) * p[2]))

                        errfunc = lambda p, x, y: modelfit(p, x) - y_data
                        p = [-4, (y_data.argmax()-1075) * self.CALIBRATE, 0.6, 0, 4 * y_data.max()]

                        p1, pcov, infodict, errmsg, success = optimize.leastsq(errfunc, p[:], args=(x_data, y_data),
                                                                               full_output=1, epsfcn=0.0001)

                        # s_sq = (errfunc(p1, x_data, y_data) ** 2).sum() / (y_data.__len__() - p.__len__())
                        # errfit = []
                        # for i in range(p1.__len__()):
                        #     errfit.append(np.absolute(pcov[i][i] ** 0.5 * s_sq))
                        self.chan_make_model_fit.setValue(0)
                        self.chan_err_mess.setValue("Model fit applied")
                        return p1, modelfit(p1, x_data), x_data

                    except OverflowError:
                        self.chan_make_model_fit.setValue(0)
                        self.chan_err_mess.setValue("OverFlow Error")
                else:
                    self.chan_err_mess.setValue("No make fit command")
                    return (0, 0, 0), y_data, x_data
            else:
                self.chan_make_model_fit.setValue(0)
                self.chan_err_mess.setValue("Curr")
                return (0, 0, 0), y_data, x_data
        else:
            self.chan_make_model_fit.setValue(0)
            self.chan_err_mess.setValue("Low signal")
            return (0, 0, 0), y_data, x_data

    @staticmethod
    def erf(x):
        erf_x = np.empty_like(x, dtype=np.float64)
        for i in range(0, x.__len__()):
            erf_x[i] = 2 * integrate.quad(lambda t: mh.exp(-t**2), 0, x[i])[0] / mh.sqrt(mh.pi)
        return erf_x

    def fit_switch(self):
        self.FIT_CHOOSE = self.chan_fit_switch.val


def main_proc():
    import cothread

    a = QtCore.QCoreApplication(sys.argv)
    app = cothread.iqt()
    w = DissApp("cxhw:18.bal333_2.line3", 'cxhw:0.e_diss')
    cothread.WaitForQuit()


def clear_proc():
    pass

a = Service('dissector', main_proc, clear_proc)