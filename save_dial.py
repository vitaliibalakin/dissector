from PyQt4 import QtCore, QtGui, uic
import sys
import datetime
import numpy as np
import pycx4.qcda as cda

class DialSave(QtGui.QDialog):
    def __init__(self):
        super(DialSave, self).__init__()
        uic.loadUi("save_dial.ui", self)

        self.chan_sigma = cda.DChan("cxhw:0.e_diss.fit_sigma")
        self.chan_cur = cda.DChan("cxhw:0.dcct.beamcurrent")

        self.chan_cur.valueMeasured.connect(self.new_val_cb)
        self.chan_sigma.valueMeasured.connect(self.new_val_cb)
        self.show()

        self.connect(self.btn_save, QtCore.SIGNAL("clicked()"), self.push_btn_save)
        self.connect(self.btn_begin_meas, QtCore.SIGNAL("clicked()"), self.begin_meas)
        self.connect(self.btn_finish_meas, QtCore.SIGNAL("clicked()"), self.finish_meas)

        self.av_num = 0

        self.cur_data = []
        self.sigma_data = []
        self.counter = {'cxhw:0.e_diss.fit_sigma': 0, 'cxhw:0.dcct.beamcurrent': 0}
        self.chans = {'cxhw:0.e_diss.fit_sigma': self.sigma_data, 'cxhw:0.dcct.beamcurrent': self.cur_data}

    def push_btn_save(self):
        self.lbl_status.setText("Saving")
        #self.counter['cxhw:0.e_diss.fit_sigma'] = self.av_num
        self.counter['cxhw:0.dcct.beamcurrent'] = self.av_num

    def new_val_cb(self, chan):
        if self.counter[chan.name] != 0:
            self.chans[chan.name][self.counter[chan.name] - 1] = chan.val
            self.counter[chan.name] -= 1
            print self.counter.values()
            if any(self.counter.values()):
                pass
            else:
                self.wr_data[0] = self.chans['cxhw:0.dcct.beamcurrent']
                self.wr_data[1] = self.chans['cxhw:0.e_diss.fit_sigma']
                np.savetxt(self.f, self.wr_data.T, delimiter=' ', newline='\n')
                self.f.write(str(self.av_num))
                self.f.write('\n')
                print(self.chans['cxhw:0.dcct.beamcurrent'])
                self.lbl_status.setText("The value was saved")
        else:
            pass

    def begin_meas(self):
        if self.ln_filename.text() != 'Write the name of file':
            date = datetime.datetime.now().strftime('%Y-%m-%d')
            self.f = open(self.ln_filename.text() + '_' + date + '.dat', 'w')
            self.av_num = self.box_av_num.value()
            self.wr_data = np.zeros((2, self.av_num), dtype=np.double)
            self.chans['cxhw:0.e_diss.fit_sigma'] = [1, 2, 3, 4,
                                                     5]  # np.zeros((self.counter['cxhw:0.e_diss.fit_sigma'],), dtype=np.double)
            self.chans['cxhw:0.dcct.beamcurrent'] = np.zeros((self.av_num,),
                                                             dtype=np.double)
            self.lbl_status.setText('Meas began')
        else:
            self.lbl_status.setText('Write the filename')

    def finish_meas(self):
        self.f.close()
        self.lbl_status.setText('Meas finished')


if __name__ == "__main__":
    app = QtGui.QApplication(['save'])
    w = DialSave()
    sys.exit(app.exec_())