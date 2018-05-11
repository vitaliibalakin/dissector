from PyQt4 import QtCore, QtGui, uic
import sys
import datetime
import numpy as np
import pycx4.qcda as cda
import json

class DialSave(QtGui.QDialog):
    def __init__(self, chan_sigma, chan_cur, chan_t0, chan_accuracy, chan_make_model_fit, chan_fit_data,
                 chan_time_fit_data):
        super(DialSave, self).__init__()
        uic.loadUi("save_dial.ui", self)

        # self.chan_sigma = cda.DChan("cxhw:0.e_diss.fit_sigma")
        # self.chan_cur = cda.DChan("cxhw:0.dcct.beamcurrent")
        # self.chan_t0 = cda.DChan("cxhw:0.e_diss.fit_t0")
        # self.chan_accuracy = cda.DChan("cxhw:0.e_diss.fit_a")

        self.chan_sigma = chan_sigma
        self.chan_cur = chan_cur
        self.chan_t0 = chan_t0
        self.chan_accuracy = chan_accuracy
        self.chan_make_model_fit = chan_make_model_fit
        self.chan_fit_data = chan_fit_data
        self.chan_time_fit_data = chan_time_fit_data

        self.chan_sigma.valueMeasured.connect(self.new_val_cb)
        self.show()

        self.connect(self.btn_save, QtCore.SIGNAL("clicked()"), self.push_btn_save)
        self.connect(self.btn_begin_meas, QtCore.SIGNAL("clicked()"), self.begin_meas)
        self.connect(self.btn_finish_meas, QtCore.SIGNAL("clicked()"), self.finish_meas)

        self.av_num = 0

        self.cur_data = []
        self.sigma_data = []
        self.accuracy = []
        self.counter = 0
        self.chans = {}

    def push_btn_save(self):
        if self.ln_filename.text() == 'Write the name of file':
            self.lbl_status.setText("No filename")
        else:
            self.lbl_status.setText("Saving")
            self.counter = self.av_num

    def new_val_cb(self):
        if self.counter != 0:
            print self.counter
            self.chans['sigma'][self.counter - 1] = self.chan_sigma.val
            self.chans['beam_current'][self.counter - 1] = self.chan_cur.val
            self.chans['t_0'][self.counter - 1] = self.chan_t0
            self.counter -= 1
            self.chan_make_model_fit.setValue(1)
            if self.counter:
                pass
            else:
                self.wr_data[0] = np.mean(self.chans['beam_current'])
                self.wr_data[1] = np.mean(self.chans['sigma'])
                self.wr_data[2] = np.mean(self.chans['t_0'])
                np.savetxt(self.f, self.wr_data.T, delimiter=' ', newline='\n')
                if self.av_num == 1:
                    self.f_osc.write(json.dump([self.chans['beam_current'], self.chan_time_fit_data,
                                                self.chan_fit_data]))
                    self.f_osc.write('\n')
                print self.wr_data.T
                self.lbl_status.setText("The value was saved")
        else:
            pass

    def begin_meas(self):
        if self.ln_filename.text() != 'Write the name of file':
            date = datetime.datetime.now().strftime('%Y-%m-%d')
            self.f = open(self.ln_filename.text() + '_' + date + '.dat', 'w')
            self.av_num = self.box_av_num.value()
            self.wr_data = np.zeros((3, 1), dtype=np.double)
            self.chans['sigma'] = np.zeros((self.av_num,), dtype=np.double)
            self.chans['beam_current'] = np.zeros((self.av_num,), dtype=np.double)
            self.chans['t_0'] = np.zeros((self.av_num,), dtype=np.double)
            if self.av_num == 1:
                self.f_osc = open('osc' + '_' + self.ln_filename.text() + '_' + date + '.dat', 'w')
            self.lbl_status.setText('Meas began')
        else:
            self.lbl_status.setText('Write the filename')

    def finish_meas(self):
        self.f.close()
        if self.av_num == 1:
            self.f_osc.close()
        self.lbl_status.setText('Meas finished')


if __name__ == "__main__":
    app = QtGui.QApplication(['save'])
    chan_sigma = cda.DChan("cxhw:0.e_diss.fit_sigma")
    chan_cur = cda.DChan("cxhw:0.dcct.beamcurrent")
    chan_t0 = cda.DChan("cxhw:0.e_diss.fit_t0")
    chan_accuracy = cda.DChan("cxhw:0.e_diss.fit_a")
    chan_make_model_fit = cda.DChan("cxhw:2.e_diss" + ".make_model_fit")
    chan_fit_data = cda.VChan('cxhw:0.e_diss' + ".fit_data", on_update=1, max_nelems=65535)
    chan_time_fit_data = cda.VChan('cxhw:0.e_diss' + ".time_fit_data", on_update=1, max_nelems=65535)
    w = DialSave(chan_sigma, chan_cur, chan_t0, chan_accuracy, chan_make_model_fit, chan_fit_data, chan_time_fit_data)
    sys.exit(app.exec_())