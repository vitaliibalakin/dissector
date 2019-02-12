#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5 import uic
import sys
import datetime
import numpy as np
import pycx4.qcda as cda
import json

class DialSave(QDialog):
    def __init__(self, chan_sigma, chan_cur, chan_t0, chan_accuracy, chan_make_model_fit, chan_fit_data,
                 chan_time_fit_data):
        super(DialSave, self).__init__()
        uic.loadUi("save_dial.ui", self)

        self.chan_sigma = chan_sigma
        self.chan_cur = chan_cur
        self.chan_t0 = chan_t0
        self.chan_accuracy = chan_accuracy
        self.chan_make_model_fit = chan_make_model_fit
        self.chan_fit_data = chan_fit_data
        self.chan_time_fit_data = chan_time_fit_data

        self.chan_sigma.valueMeasured.connect(self.new_val_cb)
        self.show()

        self.btn_save.clicked.connect(self.push_btn_save)

        self.av_num = 0
        self.sv_open = 0

        self.cur_data = []
        self.sigma_data = []
        self.accuracy = []
        self.counter = 0
        self.chans = {}
        self.wr_data = []
        self.file_name = ''
        self.osc_file_name = ''

    def push_btn_save(self):
        if not self.sv_open:
            if self.ln_filename.text() != 'Name of file':
                self.sv_open = 1
                self.av_num = self.box_av_num.value()

                date = datetime.datetime.now().strftime('%Y-%m-%d')
                self.file_name = self.ln_filename.text() + '_' + date + '.dat'
                if self.av_num == 1:
                    self.osc_file_name = self.ln_filename.text() + '_' + 'osc' + '_' + date + '.dat'

                self.wr_data = np.zeros((3, 1), dtype=np.double)
                self.chans['sigma'] = np.zeros((self.av_num,), dtype=np.double)
                self.chans['beam_current'] = np.zeros((self.av_num,), dtype=np.double)
                self.chans['t_0'] = np.zeros((self.av_num,), dtype=np.double)

                self.lbl_status.setText("Saving")
                self.counter = self.av_num
                self.chan_make_model_fit.setValue(1)
            else:
                self.lbl_status.setText("Write namefile")
        else:
            self.lbl_status.setText("Saving")
            self.counter = self.av_num
            self.chan_make_model_fit.setValue(1)

    def new_val_cb(self):
        if self.counter:
            counter = self.counter
            self.counter -= 1
            print(counter)
            self.chans['sigma'][counter - 1] = self.chan_sigma.val
            self.chans['beam_current'][counter - 1] = self.chan_cur.val
            self.chans['t_0'][counter - 1] = self.chan_t0.val
            self.chan_make_model_fit.setValue(1)
            if not self.counter:
                f = open(self.file_name, 'a')
                self.wr_data[0] = np.mean(self.chans['beam_current'])
                self.wr_data[1] = np.mean(self.chans['sigma'])
                self.wr_data[2] = np.mean(self.chans['t_0'])
                np.savetxt(f, self.wr_data.T, delimiter=' ', newline='\n')
                f.close()
                if self.av_num == 1:
                    f_osc = open(self.osc_file_name, 'a')
                    x_data = self.chan_time_fit_data.val.tolist()
                    y_data = self.chan_fit_data.val.tolist()
                    osc_data = {'current': self.chans['beam_current'][0], 'x_data': x_data, 'y_data': y_data}
                    f_osc.write(json.dumps(osc_data))
                    f_osc.write('\n')
                    f_osc.close()
                print(self.wr_data.T)
                self.lbl_status.setText("The value was saved")
        else:
            pass


if __name__ == "__main__":
    app = QApplication(['save'])
    chan_sigma = cda.DChan("cxhw:0.e_diss.fit_sigma")
    chan_cur = cda.DChan("cxhw:0.dcct.beamcurrent")
    chan_t0 = cda.DChan("cxhw:0.e_diss.fit_t0")
    chan_accuracy = cda.DChan("cxhw:0.e_diss.fit_a")
    chan_make_model_fit = cda.DChan("cxhw:2.e_diss" + ".make_model_fit")
    chan_fit_data = cda.VChan('cxhw:0.e_diss' + ".fit_data", on_update=1, max_nelems=65535)
    chan_time_fit_data = cda.VChan('cxhw:0.e_diss' + ".time_fit_data", on_update=1, max_nelems=65535)
    w = DialSave(chan_sigma, chan_cur, chan_t0, chan_accuracy, chan_make_model_fit, chan_fit_data, chan_time_fit_data)
    sys.exit(app.exec_())
