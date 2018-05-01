from PyQt4 import QtCore, QtGui, uic
import sys
import datetime
import numpy as np
import pycx4.qcda as cda

class DialSave(QtGui.QDialog):
    def __init__(self, chan_sigma, chan_cur, chan_t0, chan_accuracy):
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
        self.chans = {'cxhw:0.e_diss.fit_sigma': self.sigma_data, 'cxhw:0.dcct.beamcurrent': self.cur_data,
                      'cxhw: 0.e_diss.fit_a': self.accuracy}

    def push_btn_save(self):
        if self.ln_filename.text() == 'Write the name of file':
            self.lbl_status.setText("No filename")
        else:
            self.lbl_status.setText("Saving")
            self.counter = self.av_num

    def new_val_cb(self):
        if self.counter != 0:
            print self.counter
            self.chans['cxhw:0.e_diss.fit_sigma'][self.counter - 1] = self.chan_t0.val  # sigma -> t0
            self.chans['cxhw:0.dcct.beamcurrent'][self.counter - 1] = self.chan_cur.val
            self.chans['cxhw: 0.e_diss.fit_a'][self.counter - 1] = self.chan_accuracy
            self.counter -= 1
            if self.counter:
                pass
            else:
                self.wr_data[0] = np.mean(self.chans['cxhw:0.dcct.beamcurrent'])
                self.wr_data[1] = np.mean(self.chans['cxhw:0.e_diss.fit_sigma'])
                self.wr_data[2] = np.sqrt(np.sum(self.chans['cxhw: 0.e_diss.fit_a'] ** 2) /
                                          self.chans['cxhw: 0.e_diss.fit_a'].__len__())
                np.savetxt(self.f, self.wr_data.T, delimiter=' ', newline='\n')
                print self.wr_data.T
                #print(self.chans['cxhw:0.e_diss.fit_sigma'], self.wr_data[1], self.wr_data[2])
                #print(self.chans['cxhw:0.dcct.beamcurrent'])
                self.lbl_status.setText("The value was saved")
        else:
            pass

    def begin_meas(self):
        if self.ln_filename.text() != 'Write the name of file':
            date = datetime.datetime.now().strftime('%Y-%m-%d')
            self.f = open(self.ln_filename.text() + '_' + date + '.dat', 'w')
            self.av_num = self.box_av_num.value()
            self.wr_data = np.zeros((3, 1), dtype=np.double)
            self.chans['cxhw:0.e_diss.fit_sigma'] = np.zeros((self.av_num,), dtype=np.double)
            self.chans['cxhw:0.dcct.beamcurrent'] = np.zeros((self.av_num,), dtype=np.double)
            self.lbl_status.setText('Meas began')
        else:
            self.lbl_status.setText('Write the filename')

    def finish_meas(self):
        self.f.close()
        self.lbl_status.setText('Meas finished')


if __name__ == "__main__":
    app = QtGui.QApplication(['save'])
    chan_sigma = cda.DChan("cxhw:0.e_diss.fit_sigma")
    chan_cur = cda.DChan("cxhw:0.dcct.beamcurrent")
    chan_t0 = cda.DChan("cxhw:0.e_diss.fit_t0")
    chan_accuracy = cda.DChan("cxhw:0.e_diss.fit_a")
    w = DialSave(chan_sigma, chan_cur, chan_t0, chan_accuracy)
    sys.exit(app.exec_())