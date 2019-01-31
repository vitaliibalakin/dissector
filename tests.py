import pycx4.qcda as cda
import sys
from PyQt5.QtWidgets import QApplication


def callback(chan):
    print('callback', chan.val)


app = QApplication(['IcWatcherInfo'])
print('start')
dsm_iset = cda.DChan('canhw:12.dsm.Iset', on_update=1)
dsm_iset.valueChanged.connect(callback)
dsm_iset.setValue(400)
sys.exit(app.exec_())