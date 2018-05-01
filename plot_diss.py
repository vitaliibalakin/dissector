#!/usr/bin/python

from PyQt4 import QtGui, uic
import save_dial
import settings_dial
import sys
import numpy as np
import pyqtgraph as pg
import pycx4.qcda as cda


class PlotDissectorData(QtGui.QMainWindow):
    def __init__(self, devname):
        super(PlotDissectorData, self).__init__()
        uic.loadUi("diss_plot.ui", self)

        self.init_chans(devname)

        self.setWindowTitle("Signal from dissector")
        self.plot_window = pg.GraphicsLayoutWidget(parent=self)
        self.diss_plot = self.plot_window.addPlot(enableMenu=False)
        self.diss_plot.showGrid(x=True, y=True)
        self.diss_plot.setLabel('left', "Voltage", units='mV')
        self.diss_plot.setLabel('bottom', "Time", units='Ns')
        self.diss_plot.setRange(yRange=[-60, 300])

        p = QtGui.QHBoxLayout()
        self.plot_area.setLayout(p)
        p.addWidget(self.plot_window)

        self.btn_save.clicked.connect(self.act_save)
        self.btn_settings.clicked.connect(self.act_settings)

    def act_save(self):
        self.dial_save = save_dial.DialSave()

    def act_settings(self):
        self.dial_set = settings_dial.DialSet(self.chan_light, self.chan_phase, self.chan_ampl)

    def plot_(self, chan):
        new_size = 2150
        x_fit_data = self.chan_time_fit_data.val[0:new_size]
        y_fit_data = self.chan_fit_data.val[0:new_size]
        y_data = self.chan_thinned_data.val[0:new_size]
        #x_data = np.arange(0, new_size, 1, dtype=np.float64)

        self.sigma.setText(str(round(self.chan_sigma.val, 3)))
        #self.peak.setText(str(round(self.chan_t0.val, 3)))
        self.ampl.setText(str(round(self.chan_t0.val, 3)))
        #print(self.chan_sigma.val, self.chan_t0.val, self.chan_amplitude.val)

        self.diss_plot.clear()
        self.diss_plot.plot(x_fit_data, y_data, pen=None, symbol='o')

        if not self.show_fit.isChecked():
            self.diss_plot.plot(x_fit_data, y_fit_data, pen=pg.mkPen('r', width=5))

    def init_chans(self, devname):
        self.chan_fit_data = cda.VChan(devname + ".fit_data", max_nelems=65535)
        self.chan_thinned_data = cda.VChan(devname + ".resample_data", max_nelems=65535)
        self.chan_time_fit_data = cda.VChan(devname + ".time_fit_data", max_nelems=65535)
        self.chan_sigma = cda.DChan(devname + ".fit_sigma", on_update=1)
        self.chan_amplitude = cda.DChan(devname + ".fit_a")
        self.chan_t0 = cda.DChan(devname + ".fit_t0")
        self.chan_sigma.valueMeasured.connect(self.plot_)

        self.chan_ampl = cda.DChan("cxhw:18.diss208.out1")
        self.chan_phase = cda.DChan("cxhw:18.diss208.out0")
        self.chan_light = cda.DChan("cxhw:18.diss208.outrb0")


app = QtGui.QApplication(['plot'])
w = PlotDissectorData('cxhw:0.e_diss')
w.show()
sys.exit(app.exec_())