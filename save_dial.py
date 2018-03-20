from PyQt4 import QtCore, QtGui, uic
import sys
import numpy as np
import pycx4.qcda as cda

class DialSave(QtGui.QDialog):
    def __init__(self):
        super(DialSave, self).__init__()
        uic.loadUi("save_dial.ui", self)

        self.chan_sigma = cda.DChan("cxhw:0.e_diss.fit_sigma")
        self.chan_cur = cda.DChan("cxhw:0.dcct.beamcurrent")

        self.chan_cur.valueMeasured.connect(self.new_val_cb)
        self.show()

        self.connect(self.btn_save, QtCore.SIGNAL("clicked()"), self.push_btn_save)

        self.counter = 0
        self.cur_data = []

    def push_btn_save(self):
        self.lbl_status.setText("ok")
        self.counter = self.av_num.value()
        self.cur_data = np.zeros((self.counter,), dtype=np.double)

    def new_val_cb(self, chan):
        if self.counter != 0:
            self.cur_data[self.counter - 1] = chan.val
            self.counter -= 1
            if self.counter == 0:
                f = open("cur_data.txt", 'a')
                np.savetxt(f, self.cur_data, newline='\t')
                print(self.cur_data)
                f.write("\n")
                f.close()
                self.lbl_status.setText(str(self.cur_data[self.counter]))
        else:
            pass


if __name__ == "__main__":
    app = QtGui.QApplication(['save'])
    w = DialSave()
    sys.exit(app.exec_())