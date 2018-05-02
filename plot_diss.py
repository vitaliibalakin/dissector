#!/usr/bin/python

from PyQt4 import QtGui, uic
import save_dial
import settings_dial
import sys
import pyqtgraph as pg
import pycx4.qcda as cda


class PlotDissectorData(QtGui.QMainWindow):
    def __init__(self, devname):
        super(PlotDissectorData, self).__init__()
        uic.loadUi("diss_plot.ui", self)

        self.init_chans(devname)

        self.chan_fit_switch.setValue('gauss')
        self.rb_model_fit.setChecked(0)
        self.rb_gauss_fit.setChecked(1)

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

        # callbacks
        self.btn_save.clicked.connect(self.act_save)
        self.btn_settings.clicked.connect(self.act_settings)
        self.btn_model_run.clicked.connect(self.model_run)
        self.rb_gauss_fit.toggled.connect(self.switch_to_gauss)
        self.rb_model_fit.toggled.connect(self.switch_to_model)

    def init_chans(self, devname):
        # for drawing process
        self.chan_fit_data = cda.VChan(devname + ".fit_data", on_update=1, max_nelems=65535)
        self.chan_thinned_data = cda.VChan(devname + ".resample_data", on_update=1, max_nelems=65535)
        self.chan_time_fit_data = cda.VChan(devname + ".time_fit_data", on_update=1, max_nelems=65535)
        self.chan_sigma = cda.DChan(devname + ".fit_sigma", on_update=1)
        self.chan_accuracy = cda.DChan(devname + ".fit_a", on_update=1)
        self.chan_t0 = cda.DChan(devname + ".fit_t0", on_update=1)

        self.chan_sigma.valueChanged.connect(self.plot_)

        # for diss control
        self.chan_ampl = cda.DChan("cxhw:18.diss208.out1")
        self.chan_phase = cda.DChan("cxhw:18.diss208.out0")
        self.chan_light = cda.DChan("cxhw:18.diss208.outrb0")

        # for data saving
        self.chan_cur = cda.DChan("cxhw:0.dcct.beamcurrent")

        # for fit ctrl
        self.chan_err_mess = cda.StrChan("cxhw:2.e_diss" + ".err_mess", on_update=1, max_nelems=1024)
        self.chan_make_model_fit = cda.DChan("cxhw:2.e_diss" + ".make_model_fit")
        self.chan_fit_switch = cda.StrChan("cxhw:2.e_diss" + ".fit_switch", max_nelems=1024)

        self.chan_err_mess.valueMeasured.connect(self.err_mess)

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
        #print(self.chan_cur.val, self.chan_t0.val, self.chan_sigma.val)

    def act_save(self):
        self.dial_save = save_dial.DialSave(self.chan_sigma, self.chan_cur, self.chan_t0, self.chan_accuracy)

    def act_settings(self):
        self.dial_set = settings_dial.DialSet(self.chan_light, self.chan_phase, self.chan_ampl)

    def err_mess(self):
        self.statusbar.showMessage(self.chan_err_mess.val)

    def model_run(self):
        self.chan_make_model_fit.setValue(1)
        self.statusbar.showMessage("Model Fit pushed")

    def switch_to_gauss(self):
        self.chan_fit_switch.setValue('gauss')
        self.statusbar.showMessage('gauss')

    def switch_to_model(self):
        self.chan_fit_switch.setValue('model')
        self.statusbar.showMessage('model')


app = QtGui.QApplication(['plot'])
w = PlotDissectorData('cxhw:0.e_diss')
w.show()
sys.exit(app.exec_())