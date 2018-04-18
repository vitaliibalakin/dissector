<<<<<<< HEAD
import numpy as np
x_fit_data = np.arange(0, 2000, 1, dtype=np.float64)
x_fit_data -= x_fit_data[int(2000/2)]
x_fit_data /= 200
print (x_fit_data)
=======
from PyQt5.QtWidgets import QApplication, QMainWindow

import sys, pycx4.qcda as cda


def check():
    print(cur.val)

app = QApplication(sys.argv)
cur = cda.DChan("cxhw:0.dcct.beamcurrent")
cur.valueMeasured.connect(check)
sys.exit(app.exec_())
>>>>>>> origin/master
