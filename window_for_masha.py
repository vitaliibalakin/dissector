import numpy as np
import json

a = np.array([1, 2, 3])
c = a.tolist()
b = json.dumps(c)
print(b, a)

