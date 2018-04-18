#!/usr/bin/python

from PyQt4 import QtGui, uic
import save_dial #set_dial
import sys
import numpy as np
import pyqtgraph as pg
import pycx4.qcda as cda


class PlotDissectorData(QtGui.QMainWindow):
    def __init__(self, devname):
        super(PlotDissectorData, self).__init__()
        uic.loadUi("diss_plot.ui", self)

        self.init_chans(devname)

        self.setWindowTitle("Plot")
        self.plot_window = pg.GraphicsLayoutWidget(parent=self)
        self.diss_plot = self.plot_window.addPlot(title='Signal from dissector', enableMenu=False)
        self.diss_plot.showGrid(x=True, y=True)
        self.diss_plot.setLabel('left', "Voltage", units='mV')
        self.diss_plot.setLabel('bottom', "Time", units='Ns')
        self.diss_plot.setRange(yRange=[0, 300])

        p = QtGui.QHBoxLayout()
        self.plot_area.setLayout(p)
        p.addWidget(self.plot_window)

        self.chan_phase.valueMeasured.connect(self.init_val)        #these 6 for diss control
        self.chan_ampl.valueMeasured.connect(self.init_val)
        self.chan_light.valueMeasured.connect(self.init_val)
        self.phase_val.valueChanged.connect(self.renewal)
        self.ampl_val.valueChanged.connect(self.renewal)
        self.light.toggled.connect(self.light_switch)

        self.chan_sigma.valueMeasured.connect(self.plot_)
        self.actionSave.triggered.connect(self.act_save)
        #self.actionSettings.triggered.connect(self.act_set)

    def act_save(self):
        self.dial_save = save_dial.DialSave()

    '''def act_set(self):
        self.dial_save = set_dial.DialSet()'''

    def plot_(self):
        new_size = 2000
        x_fit_data = self.chan_time_fit_data.val[0:new_size]
        y_fit_data = self.chan_fit_data.val[0:new_size]
        y_data = self.chan_thinned_data.val[0:new_size]
        #x_data = np.arange(0, new_size, 1, dtype=np.float64)

        self.sigma.setText(str(round(self.chan_sigma.val, 3)))
        #self.peak.setText(str(round(self.chan_t0.val, 3)))
        self.ampl.setText(str(round(self.chan_t0.val, 3)))

        self.diss_plot.clear()
        self.diss_plot.plot(x_fit_data, y_data, pen=None, symbol='o')
        self.diss_plot.plot(x_fit_data, y_fit_data, pen='r')

    def init_chans(self, devname):
        self.chan_ampl = cda.DChan("cxhw:18.diss208.out1")      #these 3 for diss control
        self.chan_phase = cda.DChan("cxhw:18.diss208.out0")
        self.chan_light = cda.DChan("cxhw:18.diss208.outrb0")

        self.chan_fit_data = cda.VChan(devname + ".fit_data", max_nelems=65535)
        self.chan_thinned_data = cda.VChan(devname + ".resample_data", max_nelems=65535)
        self.chan_time_fit_data = cda.VChan(devname + ".time_fit_data", max_nelems=65535)
        self.chan_sigma = cda.DChan(devname + ".fit_sigma")
        self.chan_amplitude = cda.DChan(devname + ".fit_a")
        self.chan_t0 = cda.DChan(devname + ".fit_t0")

    def light_switch(self):                                     #for diss control
        if self.light.isChecked():
            self.chan_light.setValue(1)
            self.label_light.setText("Light ON")
        else:
            self.chan_light.setValue(0)
            self.label_light.setText("Light OFF")

    def renewal(self):                                          #for diss control
        self.chan_phase.setValue(self.phase_val.value())
        self.chan_ampl.setValue(self.ampl_val.value())

    def init_val(self):                                         #for diss control
        self.phase_val.setValue(self.chan_phase.val)
        self.ampl_val.setValue(self.chan_ampl.val)
        self.light.setChecked(self.chan_light.val)
        if self.chan_light.val:
            self.label_light.setText("Light ON")
        else:
            self.label_light.setText("Light OFF")

app = QtGui.QApplication(['plot'])
w = PlotDissectorData('cxhw:0.e_diss')
w.show()
sys.exit(app.exec_())