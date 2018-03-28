from PyQt4 import QtGui, QtCore, uic

import sys, pycx4.qcda as cda

app = QtGui.QApplication(sys.argv)
cur = cda.DChan("canhw:12.rst5.c5M4.Iset")
cur.setValue(1000)
print("ok")
sys.exit(app.exec_())