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
        self.delay = 19500
        self.FIT_CHOOSE = 'gauss'
        self.FIT_RUN = 0
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
        self.chan_err_mess = cda.StrChan("cxhw:2.e_diss" + ".err_mess", max_nelems=1024)
        self.chan_fit_switch = cda.StrChan("cxhw:2.e_diss" + ".fit_switch", on_update=1, max_nelems=1024)
        self.chan_make_model_fit = cda.DChan("cxhw:2.e_diss" + ".make_model_fit", on_update=1)

        self.chan_fit_switch.valueMeasured.connect(self.fit_switch)
        self.chan_make_model_fit.valueMeasured.connect(self.make_model_fit)

    def data_processing(self):
        y_thinned = self.thin_data(self.chan_data.val[self.delay:(self.delay+self.measured_area_size)])
        result = self.fit(self.x_fit_data, y_thinned)
        if result is not None:
            fit_param, y_fit_data, x_fit_data, b_pos, b_size = result[0], result[1], result[2], result[3], result[4]
            self.chan_thinned_data.setValue(y_thinned)
            self.chan_fit_data.setValue(y_fit_data)
            self.chan_time_fit_data.setValue(x_fit_data)
            self.chan_t0.setValue(b_pos)
            self.chan_sigma.setValue(b_size)
            # print(b_pos, fit_param[1], x_fit_data[np.argmax(y_fit_data)])

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
        if y_data.max() > 40:
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
                x_av = self.x_average(x_data, gaussfit(p1, x_data))
                beam_fwhm = self.beam_size(x_data, gaussfit(p1, x_data))
                return p1, gaussfit(p1, x_data), x_data, x_av, beam_fwhm
            elif self.FIT_CHOOSE == 'model':
                if self.FIT_RUN:
                    try:
                        modelfit = lambda p, x: p[3] + (mh.sqrt(2/mh.pi)/p[0]) * p[4] * np.exp(-(((x - p[1]) / p[2]) ** 2) / 2) / \
                                                       (mh.cosh(p[0]/2)/mh.sinh(p[0]/2) - self.erf((x - p[1]) / mh.sqrt(2) / p[2]))

                        errfunc = lambda p, x, y: modelfit(p, x) - y_data
                        p = [-3, (y_data.argmax()-1075) * self.CALIBRATE, 0.6, 0, 4 * y_data.max()]

                        p1, pcov, infodict, errmsg, success = optimize.leastsq(errfunc, p[:], args=(x_data, y_data),
                                                                               full_output=1, epsfcn=0.0001)

                        # s_sq = (errfunc(p1, x_data, y_data) ** 2).sum() / (y_data.__len__() - p.__len__())
                        # errfit = []
                        # for i in range(p1.__len__()):
                        #     errfit.append(np.absolute(pcov[i][i] ** 0.5 * s_sq))
                        self.FIT_RUN = 0
                        self.chan_make_model_fit.setValue(0)
                        x_av = self.x_average(x_data, modelfit(p1, x_data))
                        beam_fwhm = self.beam_size(x_data, modelfit(p1, x_data))
                        self.chan_err_mess.setValue("Model fit was applied")
                        return p1, modelfit(p1, x_data), x_data, x_av, beam_fwhm

                    except OverflowError:
                        self.FIT_RUN = 0
                        self.chan_err_mess.setValue("OverFlow Error. Make fit again")
                else:
                    pass
            else:
                self.FIT_RUN = 0
                self.chan_err_mess.setValue("Curr")
        else:
            self.FIT_RUN = 0
            # self.chan_err_mess.setValue("Low signal")

    @staticmethod
    def erf(x):
        erf_x = np.empty_like(x, dtype=np.float64)
        for i in range(0, len(x)):
            erf_x[i] = 2 * integrate.quad(lambda t: mh.exp(-t**2), 0, x[i])[0] / mh.sqrt(mh.pi)
        return erf_x

    @staticmethod
    def x_average(x, y):
        return integrate.trapz(x * y, x) / integrate.trapz(y, x)

    @staticmethod
    def beam_size(x, y):
        half_am = np.max(y) / 2
        x_half = np.where(y > half_am)
        beam_fwhm = x[x_half[0][-1]] - x[x_half[0][0]]
        return beam_fwhm

    def fit_switch(self):
        self.FIT_CHOOSE = self.chan_fit_switch.val

    def make_model_fit(self):
        if self.chan_make_model_fit.val:
            self.FIT_RUN = self.chan_make_model_fit.val


def main_proc():
    import cothread

    a = QtCore.QCoreApplication(sys.argv)
    app = cothread.iqt()
    w = DissApp("cxhw:18.bal333_2.line3", 'cxhw:0.e_diss')
    cothread.WaitForQuit()


def clear_proc():
    pass

a = Service('dissector', main_proc, clear_proc)