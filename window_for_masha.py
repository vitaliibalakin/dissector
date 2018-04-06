from PyQt5.QtWidgets import QApplication, QMainWindow

import sys, pycx4.qcda as cda


def check():
    print(cur.val)

app = QApplication(sys.argv)
cur = cda.DChan("cxhw:0.dcct.beamcurrent")
cur.valueMeasured.connect(check)
sys.exit(app.exec_())