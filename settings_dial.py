from PyQt4 import QtGui, uic
import sys
import pycx4.qcda as cda

class DialSet(QtGui.QDialog):
    def __init__(self):
        super(DialSet, self).__init__()
        uic.loadUi("set_dial.ui", self)

        self.chan_ampl = cda.DChan("cxhw:18.diss208.out1")
        self.chan_phase = cda.DChan("cxhw:18.diss208.out0")
        self.chan_light = cda.DChan("cxhw:18.diss208.outrb0")

        self.show()

        self.chan_phase.valueMeasured.connect(self.init_val)
        self.chan_ampl.valueMeasured.connect(self.init_val)
        self.chan_light.valueMeasured.connect(self.init_val)

        self.phase_val.valueChanged.connect(self.renewal)
        self.ampl_val.valueChanged.connect(self.renewal)
        self.light.toggled.connect(self.light_switch)

    def light_switch(self):
        if self.light.isChecked():
            self.chan_light.setValue(1)
            self.label_light.setText("Light ON")
        else:
            self.chan_light.setValue(0)
            self.label_light.setText("Light OFF")

    def renewal(self):
        self.chan_phase.setValue(self.phase_val.value())
        self.chan_ampl.setValue(self.ampl_val.value())

    def init_val(self):
        self.phase_val.setValue(self.chan_phase.val)
        self.ampl_val.setValue(self.chan_ampl.val)
        self.light.setChecked(self.chan_light.val)
        if self.chan_light.val:
            self.label_light.setText("Light ON")
        else:
            self.label_light.setText("Light OFF")


if __name__ == "__main__":
    app = QtGui.QApplication(['set'])
    w = DialSet()
    sys.exit(app.exec_())