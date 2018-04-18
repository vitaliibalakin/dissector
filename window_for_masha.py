import numpy as np
x_fit_data = np.arange(0, 2000, 1, dtype=np.float64)
x_fit_data -= x_fit_data[int(2000/2)]
x_fit_data /= 200
print (x_fit_data)