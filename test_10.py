import numpy as np
from mpl_toolkits.mplot3d import axes3d
from scipy import interpolate as ipt
import matplotlib.pyplot as plt


def calc_v(m, rho):
    return (m * 75.11**2 + 18000) / (1000 + 75.11 * m) / rho


def calc_phi(m):
    return m / (m + 1000 / 18)


def calc_c(m, rho):
    m * rho / (1000 + m * 75.11)


data = np.loadtxt('data.txt')
temperature = data[0][1:]
m = data[1:, 0]
m_inter = m
rho_t_m = [data[1:, i + 1] for i in range(len(temperature))]
rho_t_m_inter = np.ravel(rho_t_m)

for i in range(len(temperature)-1):
    m_inter = np.append(m_inter, m)

temp_interp = np.zeros([len(temperature) * len(m), ])
for i in range(len(temperature)):
    for j in range(len(m)):
        temp_interp[i*len(m) + j] = temperature[i]

phi_interp = calc_phi(m_inter)
v_interp = calc_v(m_inter, rho_t_m_inter)

# create new temp array
temp_new = np.arange(temperature[0], temperature[4], 1)
# create new m array
m_new = m
for i in range(len(temp_new)-1):
    m_new = np.append(m_new, m)

temp_plot = np.zeros([len(temp_new) * len(m), ])
for i in range(len(temp_new)):
    for j in range(len(m)):
        temp_plot[i * len(m) + j] = temp_new[i]

phi = calc_phi(m)
f_inter = ipt.interp2d(phi_interp, temp_interp, v_interp, kind='cubic')

phi_new_plot = calc_phi(m_new)
v_new = np.ravel(f_inter(phi, temp_new))

print(len(phi_new_plot), len(temp_plot), len(v_new))

fig = plt.figure()
ax = fig.add_subplot(121, projection='3d')
ax.plot_trisurf(phi_interp, temp_interp, v_interp)
ax.set_xlabel('phi_m')
ax.set_ylabel('temperature')
ax.set_zlabel('Volume')

bx = fig.add_subplot(122, projection='3d')
bx.plot_trisurf(phi_new_plot, temp_plot, v_new)
bx.set_xlabel('phi_m')
bx.set_ylabel('temperature')
bx.set_zlabel('Volume')
plt.show()
