#!/usr/bin/python

import numpy as np
from scipy import optimize
from scipy import interpolate
from aux.service_daemon import CXService
import os
import pycx4.pycda as cda
import json


class KickerApp(object):
    def __init__(self):
        super(KickerApp, self).__init__()

        self.init_chans()

        self.list_GC = [self.chan_Ugood_ppn, self.chan_Ugood_kpn, self.chan_Ugood_ppp, self.chan_Ugood_kpp,
                        self.chan_Ugood_pen, self.chan_Ugood_ken, self.chan_Ugood_pep, self.chan_Ugood_kep]
        self.list_TC = [self.chan_Utemp_ppn, self.chan_Utemp_kpn, self.chan_Utemp_ppp, self.chan_Utemp_kpp,
                        self.chan_Utemp_pen, self.chan_Utemp_ken, self.chan_Utemp_pep, self.chan_Utemp_kep]
        self.list_DT = [self.chan_delta_arr_ppn, self.chan_delta_arr_kpn, self.chan_delta_arr_ppp,
                        self.chan_delta_arr_kpp, self.chan_delta_arr_pen, self.chan_delta_arr_ken,
                        self.chan_delta_arr_pep, self.chan_delta_arr_kep]
        self.list_SIG = [self.chan_sigma_t_ppn, self.chan_sigma_t_kpn, self.chan_sigma_t_ppp,
                         self.chan_sigma_t_kpp, self.chan_sigma_t_pen, self.chan_sigma_t_ken,
                         self.chan_sigma_t_pep, self.chan_sigma_t_kep]

        self.u_data_good = np.zeros((76,), dtype=np.double)
        self.u_data = np.zeros((76,), dtype=np.double)
        self.t_data_good = np.zeros((76,), dtype=np.double)
        self.fit_data = np.zeros((76,), dtype=np.double)

        self.n_interp = 20
        self.STEP = 5.13 / self.n_interp

        self.ic_mode = ''
        self.active_tab = {'p': 1, 'e': 0}
        self.hist_ctrl = {"cxhw:2.inj.prekick.p.neg.histo_range": 5, "cxhw:2.inj.prekick.p.neg.n_interp": 10}

        self.ki_time = np.zeros((75 * self.n_interp,), dtype=np.double)
        self.ki_amp_g = np.zeros((75 * self.n_interp,), dtype=np.double)  # g = good
        self.ki_amp_c = np.zeros((75 * self.n_interp,), dtype=np.double)  # c = compare

        self.T = np.zeros((1024,), dtype=np.double)                       # time array
        for i in range(0, 1024):
            self.T[i] = 5 * i

        self.chan_pp.valueChanged.connect(self.data_proc)
        self.chan_pn.valueChanged.connect(self.data_proc)
        self.chan_kp.valueChanged.connect(self.data_proc)
        self.chan_kn.valueChanged.connect(self.data_proc)
        self.cmd_chan.valueMeasured.connect(self.daemon_cmd)
        self.chan_ic_mode.valueChanged.connect(self.kkr_sel)
        self.chan_n_interp_ppn.valueChanged.connect(self.hist_tun)
        self.chan_histo_range_ppn.valueChanged.connect(self.hist_tun)
        print("prog_start")
        print(os.getcwd())

    def init_chans(self):
        self.chan_adc200_ptsofs_1 = cda.DChan("cxhw:18.adc200_kkr1.ptsofs")
        self.chan_adc200_ptsofs_2 = cda.DChan("cxhw:18.adc200_kkr2.ptsofs")
        self.chan_adc200_numpts_1 = cda.DChan("cxhw:18.adc200_kkr1.numpts")
        self.chan_adc200_numpts_2 = cda.DChan("cxhw:18.adc200_kkr2.numpts")
        self.chan_adc200_timing_1 = cda.DChan("cxhw:18.adc200_kkr1.timing")
        self.chan_adc200_timing_2 = cda.DChan("cxhw:18.adc200_kkr2.timing")
        self.chan_adc200_frq_div_1 = cda.DChan("cxhw:18.adc200_kkr1.frqdiv")
        self.chan_adc200_frq_div_2 = cda.DChan("cxhw:18.adc200_kkr2.frqdiv")
        self.chan_adc200_range_1_1 = cda.DChan("cxhw:18.adc200_kkr1.range1")
        self.chan_adc200_range_1_2 = cda.DChan("cxhw:18.adc200_kkr1.range2")
        self.chan_adc200_range_2_1 = cda.DChan("cxhw:18.adc200_kkr2.range1")
        self.chan_adc200_range_2_2 = cda.DChan("cxhw:18.adc200_kkr2.range2")

        self.chan_pp = cda.VChan("cxhw:18.adc200_kkr1.line1", max_nelems=424)
        self.chan_pn = cda.VChan("cxhw:18.adc200_kkr1.line2", max_nelems=424)
        self.chan_kp = cda.VChan("cxhw:18.adc200_kkr2.line1", max_nelems=424)
        self.chan_kn = cda.VChan("cxhw:18.adc200_kkr2.line2", max_nelems=424)

        self.chan_sel_all = cda.DChan("cxhw:18.kkr_sel_all.0")

        self.cmd_chan = cda.StrChan("cxhw:2.kickADCproc.inj.cmd@u")
        self.res_chan = cda.StrChan("cxhw:2.kickADCproc.inj.res@u")

        self.chan_ic_mode = cda.StrChan("cxhw:0.k500.modet", max_nelems=4)

        self.chan_Tgood_ppn = cda.VChan("cxhw:2.inj.prekick.p.neg.Tgood", max_nelems=1024)  # positrons "-" prekick
        self.chan_Ugood_ppn = cda.VChan("cxhw:2.inj.prekick.p.neg.Ugood", max_nelems=1024)
        self.chan_Ttemp_ppn = cda.VChan("cxhw:2.inj.prekick.p.neg.Ttemp", max_nelems=1024)
        self.chan_Utemp_ppn = cda.VChan("cxhw:2.inj.prekick.p.neg.Utemp", max_nelems=1024)
        self.chan_delta_a_ppn = cda.DChan("cxhw:2.inj.prekick.p.neg.delta_a")
        self.chan_delta_t_ppn = cda.DChan("cxhw:2.inj.prekick.p.neg.delta_t")
        self.chan_n_interp_ppn = cda.DChan("cxhw:2.inj.prekick.p.neg.n_interp")
        self.chan_sigma_t_ppn = cda.DChan("cxhw:2.inj.prekick.p.neg.sigma_cur")
        self.chan_delta_arr_ppn = cda.VChan("cxhw:2.inj.prekick.p.neg.delta_t_array", max_nelems=100)
        self.chan_t_peak_ppn = cda.DChan("cxhw:2.inj.prekick.p.neg.t_peak")
        self.chan_histo_range_ppn = cda.DChan("cxhw:2.inj.prekick.p.neg.histo_range")
        self.chan_histo_x_all_ppn = cda.VChan("cxhw:2.inj.prekick.p.neg.histo_x_all", max_nelems=100)
        self.chan_histo_y_all_ppn = cda.VChan("cxhw:2.inj.prekick.p.neg.histo_y_all", max_nelems=100)
        self.chan_histo_x_1_ppn = cda.VChan("cxhw:2.inj.prekick.p.neg.histo_x_1", max_nelems=101)
        self.chan_histo_y_1_ppn = cda.VChan("cxhw:2.inj.prekick.p.neg.histo_y_1", max_nelems=101)
        self.chan_histo_x_2_ppn = cda.VChan("cxhw:2.inj.prekick.p.neg.histo_x_2", max_nelems=101)
        self.chan_histo_y_2_ppn = cda.VChan("cxhw:2.inj.prekick.p.neg.histo_y_2", max_nelems=101)
        self.chan_histo_x_3_ppn = cda.VChan("cxhw:2.inj.prekick.p.neg.histo_x_3", max_nelems=101)
        self.chan_histo_y_3_ppn = cda.VChan("cxhw:2.inj.prekick.p.neg.histo_y_3", max_nelems=101)
        self.chan_abs_a_good_ppn = cda.DChan("cxhw:2.inj.prekick.p.neg.abs_a_good")

        self.chan_Tgood_kpn = cda.VChan("cxhw:2.inj.kick.p.neg.Tgood", max_nelems=1024)  # positrons "-" kick
        self.chan_Ugood_kpn = cda.VChan("cxhw:2.inj.kick.p.neg.Ugood", max_nelems=1024)
        self.chan_Ttemp_kpn = cda.VChan("cxhw:2.inj.kick.p.neg.Ttemp", max_nelems=1024)
        self.chan_Utemp_kpn = cda.VChan("cxhw:2.inj.kick.p.neg.Utemp", max_nelems=1024)
        self.chan_delta_a_kpn = cda.DChan("cxhw:2.inj.kick.p.neg.delta_a")
        self.chan_delta_t_kpn = cda.DChan("cxhw:2.inj.kick.p.neg.delta_t")
        self.chan_n_interp_kpn = cda.DChan("cxhw:2.inj.kick.p.neg.n_interp")
        self.chan_sigma_t_kpn = cda.DChan("cxhw:2.inj.kick.p.neg.sigma_cur")
        self.chan_delta_arr_kpn = cda.VChan("cxhw:2.inj.kick.p.neg.delta_t_array", max_nelems=200)
        self.chan_t_peak_kpn = cda.DChan("cxhw:2.inj.kick.p.neg.t_peak")
        self.chan_histo_x_all_kpn = cda.VChan("cxhw:2.inj.kick.p.neg.histo_x_all", max_nelems=100)
        self.chan_histo_y_all_kpn = cda.VChan("cxhw:2.inj.kick.p.neg.histo_y_all", max_nelems=100)
        self.chan_histo_x_1_kpn = cda.VChan("cxhw:2.inj.kick.p.neg.histo_x_1", max_nelems=101)
        self.chan_histo_y_1_kpn = cda.VChan("cxhw:2.inj.kick.p.neg.histo_y_1", max_nelems=101)
        self.chan_histo_x_2_kpn = cda.VChan("cxhw:2.inj.kick.p.neg.histo_x_2", max_nelems=101)
        self.chan_histo_y_2_kpn = cda.VChan("cxhw:2.inj.kick.p.neg.histo_y_2", max_nelems=101)
        self.chan_histo_x_3_kpn = cda.VChan("cxhw:2.inj.kick.p.neg.histo_x_3", max_nelems=101)
        self.chan_histo_y_3_kpn = cda.VChan("cxhw:2.inj.kick.p.neg.histo_y_3", max_nelems=101)
        self.chan_abs_a_good_kpn = cda.DChan("cxhw:2.inj.kick.p.neg.abs_a_good")

        self.chan_Tgood_ppp = cda.VChan("cxhw:2.inj.prekick.p.pos.Tgood", max_nelems=1024)  # positrons "+" prekick
        self.chan_Ugood_ppp = cda.VChan("cxhw:2.inj.prekick.p.pos.Ugood", max_nelems=1024)
        self.chan_Ttemp_ppp = cda.VChan("cxhw:2.inj.prekick.p.pos.Ttemp", max_nelems=1024)
        self.chan_Utemp_ppp = cda.VChan("cxhw:2.inj.prekick.p.pos.Utemp", max_nelems=1024)
        self.chan_delta_a_ppp = cda.DChan("cxhw:2.inj.prekick.p.pos.delta_a")
        self.chan_delta_t_ppp = cda.DChan("cxhw:2.inj.prekick.p.pos.delta_t")
        self.chan_n_interp_ppp = cda.DChan("cxhw:2.inj.prekick.p.pos.n_interp")
        self.chan_sigma_t_ppp = cda.DChan("cxhw:2.inj.prekick.p.pos.sigma_cur")
        self.chan_delta_arr_ppp = cda.VChan("cxhw:2.inj.prekick.p.pos.delta_t_array", max_nelems=200)
        self.chan_t_peak_ppp = cda.DChan("cxhw:2.inj.prekick.p.pos.t_peak")
        self.chan_histo_x_all_ppp = cda.VChan("cxhw:2.inj.prekick.p.pos.histo_x_all", max_nelems=100)
        self.chan_histo_y_all_ppp = cda.VChan("cxhw:2.inj.prekick.p.pos.histo_y_all", max_nelems=100)
        self.chan_histo_x_1_ppp = cda.VChan("cxhw:2.inj.prekick.p.pos.histo_x_1", max_nelems=101)
        self.chan_histo_y_1_ppp = cda.VChan("cxhw:2.inj.prekick.p.pos.histo_y_1", max_nelems=101)
        self.chan_histo_x_2_ppp = cda.VChan("cxhw:2.inj.prekick.p.pos.histo_x_2", max_nelems=101)
        self.chan_histo_y_2_ppp = cda.VChan("cxhw:2.inj.prekick.p.pos.histo_y_2", max_nelems=101)
        self.chan_histo_x_3_ppp = cda.VChan("cxhw:2.inj.prekick.p.pos.histo_x_3", max_nelems=101)
        self.chan_histo_y_3_ppp = cda.VChan("cxhw:2.inj.prekick.p.pos.histo_y_3", max_nelems=101)
        self.chan_abs_a_good_ppp = cda.DChan("cxhw:2.inj.prekick.p.pos.abs_a_good")

        self.chan_Tgood_kpp = cda.VChan("cxhw:2.inj.kick.p.pos.Tgood", max_nelems=1024)  # positrons "+" kick
        self.chan_Ugood_kpp = cda.VChan("cxhw:2.inj.kick.p.pos.Ugood", max_nelems=1024)
        self.chan_Ttemp_kpp = cda.VChan("cxhw:2.inj.kick.p.pos.Ttemp", max_nelems=1024)
        self.chan_Utemp_kpp = cda.VChan("cxhw:2.inj.kick.p.pos.Utemp", max_nelems=1024)
        self.chan_delta_a_kpp = cda.DChan("cxhw:2.inj.kick.p.pos.delta_a")
        self.chan_delta_t_kpp = cda.DChan("cxhw:2.inj.kick.p.pos.delta_t")
        self.chan_n_interp_kpp = cda.DChan("cxhw:2.inj.kick.p.pos.n_interp")
        self.chan_sigma_t_kpp = cda.DChan("cxhw:2.inj.kick.p.pos.sigma_cur")
        self.chan_delta_arr_kpp = cda.VChan("cxhw:2.inj.kick.p.pos.delta_t_array", max_nelems=200)
        self.chan_t_peak_kpp = cda.DChan("cxhw:2.inj.kick.p.pos.t_peak")
        self.chan_histo_x_all_kpp = cda.VChan("cxhw:2.inj.kick.p.pos.histo_x_all", max_nelems=100)
        self.chan_histo_y_all_kpp = cda.VChan("cxhw:2.inj.kick.p.pos.histo_y_all", max_nelems=100)
        self.chan_histo_x_1_kpp = cda.VChan("cxhw:2.inj.kick.p.pos.histo_x_1", max_nelems=101)
        self.chan_histo_y_1_kpp = cda.VChan("cxhw:2.inj.kick.p.pos.histo_y_1", max_nelems=101)
        self.chan_histo_x_2_kpp = cda.VChan("cxhw:2.inj.kick.p.pos.histo_x_2", max_nelems=101)
        self.chan_histo_y_2_kpp = cda.VChan("cxhw:2.inj.kick.p.pos.histo_y_2", max_nelems=101)
        self.chan_histo_x_3_kpp = cda.VChan("cxhw:2.inj.kick.p.pos.histo_x_3", max_nelems=101)
        self.chan_histo_y_3_kpp = cda.VChan("cxhw:2.inj.kick.p.pos.histo_y_3", max_nelems=101)
        self.chan_abs_a_good_kpp = cda.DChan("cxhw:2.inj.kick.p.pos.abs_a_good")

        self.chan_Tgood_pen = cda.VChan("cxhw:2.inj.prekick.e.neg.Tgood", max_nelems=1024)  # electrons "-" prekick
        self.chan_Ugood_pen = cda.VChan("cxhw:2.inj.prekick.e.neg.Ugood", max_nelems=1024)
        self.chan_Ttemp_pen = cda.VChan("cxhw:2.inj.prekick.e.neg.Ttemp", max_nelems=1024)
        self.chan_Utemp_pen = cda.VChan("cxhw:2.inj.prekick.e.neg.Utemp", max_nelems=1024)
        self.chan_delta_a_pen = cda.DChan("cxhw:2.inj.prekick.e.neg.delta_a")
        self.chan_delta_t_pen = cda.DChan("cxhw:2.inj.prekick.e.neg.delta_t")
        self.chan_n_interp_pen = cda.DChan("cxhw:2.inj.prekick.e.neg.n_interp")
        self.chan_sigma_t_pen = cda.DChan("cxhw:2.inj.prekick.e.neg.sigma_cur")
        self.chan_delta_arr_pen = cda.VChan("cxhw:2.inj.prekick.e.neg.delta_t_array", max_nelems=200)
        self.chan_t_peak_pen = cda.DChan("cxhw:2.inj.prekick.e.neg.t_peak")
        self.chan_histo_x_all_pen = cda.VChan("cxhw:2.inj.prekick.e.neg.histo_x_all", max_nelems=100)
        self.chan_histo_y_all_pen = cda.VChan("cxhw:2.inj.prekick.e.neg.histo_y_all", max_nelems=100)
        self.chan_histo_x_1_pen = cda.VChan("cxhw:2.inj.prekick.e.neg.histo_x_1", max_nelems=101)
        self.chan_histo_y_1_pen = cda.VChan("cxhw:2.inj.prekick.e.neg.histo_y_1", max_nelems=101)
        self.chan_histo_x_2_pen = cda.VChan("cxhw:2.inj.prekick.e.neg.histo_x_2", max_nelems=101)
        self.chan_histo_y_2_pen = cda.VChan("cxhw:2.inj.prekick.e.neg.histo_y_2", max_nelems=101)
        self.chan_histo_x_3_pen = cda.VChan("cxhw:2.inj.prekick.e.neg.histo_x_3", max_nelems=101)
        self.chan_histo_y_3_pen = cda.VChan("cxhw:2.inj.prekick.e.neg.histo_y_3", max_nelems=101)
        self.chan_abs_a_good_pen = cda.DChan("cxhw:2.inj.prekick.e.neg.abs_a_good")

        self.chan_Tgood_ken = cda.VChan("cxhw:2.inj.kick.e.neg.Tgood", max_nelems=1024)  # electrons "-" kick
        self.chan_Ugood_ken = cda.VChan("cxhw:2.inj.kick.e.neg.Ugood", max_nelems=1024)
        self.chan_Ttemp_ken = cda.VChan("cxhw:2.inj.kick.e.neg.Ttemp", max_nelems=1024)
        self.chan_Utemp_ken = cda.VChan("cxhw:2.inj.kick.e.neg.Utemp", max_nelems=1024)
        self.chan_delta_a_ken = cda.DChan("cxhw:2.inj.kick.e.neg.delta_a")
        self.chan_delta_t_ken = cda.DChan("cxhw:2.inj.kick.e.neg.delta_t")
        self.chan_n_interp_ken = cda.DChan("cxhw:2.inj.kick.e.neg.n_interp")
        self.chan_sigma_t_ken = cda.DChan("cxhw:2.inj.kick.e.neg.sigma_cur")
        self.chan_delta_arr_ken = cda.VChan("cxhw:2.inj.kick.e.neg.delta_t_array", max_nelems=200)
        self.chan_t_peak_ken = cda.DChan("cxhw:2.inj.kick.e.neg.t_peak")
        self.chan_histo_x_all_ken = cda.VChan("cxhw:2.inj.kick.e.neg.histo_x_all", max_nelems=100)
        self.chan_histo_y_all_ken = cda.VChan("cxhw:2.inj.kick.e.neg.histo_y_all", max_nelems=100)
        self.chan_histo_x_1_ken = cda.VChan("cxhw:2.inj.kick.e.neg.histo_x_1", max_nelems=101)
        self.chan_histo_y_1_ken = cda.VChan("cxhw:2.inj.kick.e.neg.histo_y_1", max_nelems=101)
        self.chan_histo_x_2_ken = cda.VChan("cxhw:2.inj.kick.e.neg.histo_x_2", max_nelems=101)
        self.chan_histo_y_2_ken = cda.VChan("cxhw:2.inj.kick.e.neg.histo_y_2", max_nelems=101)
        self.chan_histo_x_3_ken = cda.VChan("cxhw:2.inj.kick.e.neg.histo_x_3", max_nelems=101)
        self.chan_histo_y_3_ken = cda.VChan("cxhw:2.inj.kick.e.neg.histo_y_3", max_nelems=101)
        self.chan_abs_a_good_ken = cda.DChan("cxhw:2.inj.kick.e.neg.abs_a_good")

        self.chan_Tgood_pep = cda.VChan("cxhw:2.inj.prekick.e.pos.Tgood", max_nelems=1024)  # electrons "+" prekick
        self.chan_Ugood_pep = cda.VChan("cxhw:2.inj.prekick.e.pos.Ugood", max_nelems=1024)
        self.chan_Ttemp_pep = cda.VChan("cxhw:2.inj.prekick.e.pos.Ttemp", max_nelems=1024)
        self.chan_Utemp_pep = cda.VChan("cxhw:2.inj.prekick.e.pos.Utemp", max_nelems=1024)
        self.chan_delta_a_pep = cda.DChan("cxhw:2.inj.prekick.e.pos.delta_a")
        self.chan_delta_t_pep = cda.DChan("cxhw:2.inj.prekick.e.pos.delta_t")
        self.chan_n_interp_pep = cda.DChan("cxhw:2.inj.prekick.e.pos.n_interp")
        self.chan_sigma_t_pep = cda.DChan("cxhw:2.inj.prekick.e.pos.sigma_cur")
        self.chan_delta_arr_pep = cda.VChan("cxhw:2.inj.prekick.e.pos.delta_t_array", max_nelems=200)
        self.chan_t_peak_pep = cda.DChan("cxhw:2.inj.prekick.e.pos.t_peak")
        self.chan_histo_x_all_pep = cda.VChan("cxhw:2.inj.prekick.e.pos.histo_x_all", max_nelems=100)
        self.chan_histo_y_all_pep = cda.VChan("cxhw:2.inj.prekick.e.pos.histo_y_all", max_nelems=100)
        self.chan_histo_x_1_pep = cda.VChan("cxhw:2.inj.prekick.e.pos.histo_x_1", max_nelems=101)
        self.chan_histo_y_1_pep = cda.VChan("cxhw:2.inj.prekick.e.pos.histo_y_1", max_nelems=101)
        self.chan_histo_x_2_pep = cda.VChan("cxhw:2.inj.prekick.e.pos.histo_x_2", max_nelems=101)
        self.chan_histo_y_2_pep = cda.VChan("cxhw:2.inj.prekick.e.pos.histo_y_2", max_nelems=101)
        self.chan_histo_x_3_pep = cda.VChan("cxhw:2.inj.prekick.e.pos.histo_x_3", max_nelems=101)
        self.chan_histo_y_3_pep = cda.VChan("cxhw:2.inj.prekick.e.pos.histo_y_3", max_nelems=101)
        self.chan_abs_a_good_pep = cda.DChan("cxhw:2.inj.prekick.e.pos.abs_a_good")

        self.chan_Tgood_kep = cda.VChan("cxhw:2.inj.kick.e.pos.Tgood", max_nelems=1024)  # electrons "+" kick
        self.chan_Ugood_kep = cda.VChan("cxhw:2.inj.kick.e.pos.Ugood", max_nelems=1024)
        self.chan_Ttemp_kep = cda.VChan("cxhw:2.inj.kick.e.pos.Ttemp", max_nelems=1024)
        self.chan_Utemp_kep = cda.VChan("cxhw:2.inj.kick.e.pos.Utemp", max_nelems=1024)
        self.chan_delta_a_kep = cda.DChan("cxhw:2.inj.kick.e.pos.delta_a")
        self.chan_delta_t_kep = cda.DChan("cxhw:2.inj.kick.e.pos.delta_t")
        self.chan_n_interp_kep = cda.DChan("cxhw:2.inj.kick.e.pos.n_interp")
        self.chan_sigma_t_kep = cda.DChan("cxhw:2.inj.kick.e.pos.sigma_cur")
        self.chan_delta_arr_kep = cda.VChan("cxhw:2.inj.kick.e.pos.delta_t_array", max_nelems=200)
        self.chan_t_peak_kep = cda.DChan("cxhw:2.inj.kick.e.pos.t_peak")
        self.chan_histo_x_all_kep = cda.VChan("cxhw:2.inj.kick.e.pos.histo_x_all", max_nelems=100)
        self.chan_histo_y_all_kep = cda.VChan("cxhw:2.inj.kick.e.pos.histo_y_all", max_nelems=100)
        self.chan_histo_x_1_kep = cda.VChan("cxhw:2.inj.kick.e.pos.histo_x_1", max_nelems=101)
        self.chan_histo_y_1_kep = cda.VChan("cxhw:2.inj.kick.e.pos.histo_y_1", max_nelems=101)
        self.chan_histo_x_2_kep = cda.VChan("cxhw:2.inj.kick.e.pos.histo_x_2", max_nelems=101)
        self.chan_histo_y_2_kep = cda.VChan("cxhw:2.inj.kick.e.pos.histo_y_2", max_nelems=101)
        self.chan_histo_x_3_kep = cda.VChan("cxhw:2.inj.kick.e.pos.histo_x_3", max_nelems=101)
        self.chan_histo_y_3_kep = cda.VChan("cxhw:2.inj.kick.e.pos.histo_y_3", max_nelems=101)
        self.chan_abs_a_good_kep = cda.DChan("cxhw:2.inj.kick.e.pos.abs_a_good")

        self.list_hist_ppp = [self.chan_histo_x_all_ppp, self.chan_histo_y_all_ppp, self.chan_histo_x_1_ppp,
                              self.chan_histo_y_1_ppp, self.chan_histo_x_2_ppp, self.chan_histo_y_2_ppp,
                              self.chan_histo_x_3_ppp, self.chan_histo_y_3_ppp]
        self.list_hist_ppn = [self.chan_histo_x_all_ppn, self.chan_histo_y_all_ppn, self.chan_histo_x_1_ppn,
                              self.chan_histo_y_1_ppn, self.chan_histo_x_2_ppn, self.chan_histo_y_2_ppn,
                              self.chan_histo_x_3_ppn, self.chan_histo_y_3_ppn]
        self.list_hist_kpp = [self.chan_histo_x_all_kpp, self.chan_histo_y_all_kpp, self.chan_histo_x_1_kpp,
                              self.chan_histo_y_1_kpp, self.chan_histo_x_2_kpp, self.chan_histo_y_2_kpp,
                              self.chan_histo_x_3_kpp, self.chan_histo_y_3_kpp]
        self.list_hist_kpn = [self.chan_histo_x_all_kpn, self.chan_histo_y_all_kpn, self.chan_histo_x_1_kpn,
                              self.chan_histo_y_1_kpn, self.chan_histo_x_2_kpn, self.chan_histo_y_2_kpn,
                              self.chan_histo_x_3_kpn, self.chan_histo_y_3_kpn]
        self.list_hist_pep = [self.chan_histo_x_all_pep, self.chan_histo_y_all_pep, self.chan_histo_x_1_pep,
                              self.chan_histo_y_1_pep, self.chan_histo_x_2_pep, self.chan_histo_y_2_pep,
                              self.chan_histo_x_3_ppp, self.chan_histo_y_3_ppp]
        self.list_hist_pen = [self.chan_histo_x_all_pen, self.chan_histo_y_all_pen, self.chan_histo_x_1_pen,
                              self.chan_histo_y_1_pen, self.chan_histo_x_2_pen, self.chan_histo_y_2_pen,
                              self.chan_histo_x_3_pen, self.chan_histo_y_3_pen]
        self.list_hist_kep = [self.chan_histo_x_all_kep, self.chan_histo_y_all_kep, self.chan_histo_x_1_kep,
                              self.chan_histo_y_1_kep, self.chan_histo_x_2_kep, self.chan_histo_y_2_kep,
                              self.chan_histo_x_3_kep, self.chan_histo_y_3_kep]
        self.list_hist_ken = [self.chan_histo_x_all_ken, self.chan_histo_y_all_ken, self.chan_histo_x_1_ken,
                              self.chan_histo_y_1_ken, self.chan_histo_x_2_ken, self.chan_histo_y_2_ken,
                              self.chan_histo_x_3_ken, self.chan_histo_y_3_ken]

        self.dict_hist = {'cxhw:18.adc200_kkr1.line1p': self.list_hist_ppp,
                          'cxhw:18.adc200_kkr1.line2p': self.list_hist_ppn,
                          'cxhw:18.adc200_kkr2.line1p': self.list_hist_kpp,
                          'cxhw:18.adc200_kkr2.line2p': self.list_hist_kpn,
                          'cxhw:18.adc200_kkr1.line1e': self.list_hist_pep,
                          'cxhw:18.adc200_kkr1.line2e': self.list_hist_pen,
                          'cxhw:18.adc200_kkr2.line1e': self.list_hist_kep,
                          'cxhw:18.adc200_kkr2.line2e': self.list_hist_ken}
        self.dict_good_chans = {'cxhw:18.adc200_kkr1.line1p': self.chan_Ugood_ppp,
                                'cxhw:18.adc200_kkr1.line2p': self.chan_Ugood_ppn,
                                'cxhw:18.adc200_kkr2.line1p': self.chan_Ugood_kpp,
                                'cxhw:18.adc200_kkr2.line2p': self.chan_Ugood_kpn,
                                'cxhw:18.adc200_kkr1.line1e': self.chan_Ugood_pep,
                                'cxhw:18.adc200_kkr1.line2e': self.chan_Ugood_pen,
                                'cxhw:18.adc200_kkr2.line1e': self.chan_Ugood_kep,
                                'cxhw:18.adc200_kkr2.line2e': self.chan_Ugood_ken}
        self.dict_temp_chans = {'cxhw:18.adc200_kkr1.line1p': self.chan_Utemp_ppp,
                                'cxhw:18.adc200_kkr1.line2p': self.chan_Utemp_ppn,
                                'cxhw:18.adc200_kkr2.line1p': self.chan_Utemp_kpp,
                                'cxhw:18.adc200_kkr2.line2p': self.chan_Utemp_kpn,
                                'cxhw:18.adc200_kkr1.line1e': self.chan_Utemp_pep,
                                'cxhw:18.adc200_kkr1.line2e': self.chan_Utemp_pen,
                                'cxhw:18.adc200_kkr2.line1e': self.chan_Utemp_kep,
                                'cxhw:18.adc200_kkr2.line2e': self.chan_Utemp_ken}
        self.dict_delta_t = {'cxhw:18.adc200_kkr1.line1p': self.chan_delta_t_ppp,
                             'cxhw:18.adc200_kkr1.line2p': self.chan_delta_t_ppn,
                             'cxhw:18.adc200_kkr2.line1p': self.chan_delta_t_kpp,
                             'cxhw:18.adc200_kkr2.line2p': self.chan_delta_t_kpn,
                             'cxhw:18.adc200_kkr1.line1e': self.chan_delta_t_pep,
                             'cxhw:18.adc200_kkr1.line2e': self.chan_delta_t_pen,
                             'cxhw:18.adc200_kkr2.line1e': self.chan_delta_t_kep,
                             'cxhw:18.adc200_kkr2.line2e': self.chan_delta_t_ken}
        self.dict_delta_arr = {'cxhw:18.adc200_kkr1.line1p': self.chan_delta_arr_ppp,
                               'cxhw:18.adc200_kkr1.line2p': self.chan_delta_arr_ppn,
                               'cxhw:18.adc200_kkr2.line1p': self.chan_delta_arr_kpp,
                               'cxhw:18.adc200_kkr2.line2p': self.chan_delta_arr_kpn,
                               'cxhw:18.adc200_kkr1.line1e': self.chan_delta_arr_pep,
                               'cxhw:18.adc200_kkr1.line2e': self.chan_delta_arr_pen,
                               'cxhw:18.adc200_kkr2.line1e': self.chan_delta_arr_kep,
                               'cxhw:18.adc200_kkr2.line2e': self.chan_delta_arr_ken}
        self.dict_sigma_t = {'cxhw:18.adc200_kkr1.line1p': self.chan_sigma_t_ppp,
                             'cxhw:18.adc200_kkr1.line2p': self.chan_sigma_t_ppn,
                             'cxhw:18.adc200_kkr2.line1p': self.chan_sigma_t_kpp,
                             'cxhw:18.adc200_kkr2.line2p': self.chan_sigma_t_kpn,
                             'cxhw:18.adc200_kkr1.line1e': self.chan_sigma_t_pep,
                             'cxhw:18.adc200_kkr1.line2e': self.chan_sigma_t_pen,
                             'cxhw:18.adc200_kkr2.line1e': self.chan_sigma_t_kep,
                             'cxhw:18.adc200_kkr2.line2e': self.chan_sigma_t_ken}
        self.dict_t_peak = {'cxhw:18.adc200_kkr1.line1p': self.chan_t_peak_ppp,
                            'cxhw:18.adc200_kkr1.line2p': self.chan_t_peak_ppn,
                            'cxhw:18.adc200_kkr2.line1p': self.chan_t_peak_kpp,
                            'cxhw:18.adc200_kkr2.line2p': self.chan_t_peak_kpn,
                            'cxhw:18.adc200_kkr1.line1e': self.chan_t_peak_pep,
                            'cxhw:18.adc200_kkr1.line2e': self.chan_t_peak_pen,
                            'cxhw:18.adc200_kkr2.line1e': self.chan_t_peak_kep,
                            'cxhw:18.adc200_kkr2.line2e': self.chan_t_peak_ken}

    def hist_tun(self, chan):
        self.hist_ctrl[chan.name] = int(chan.val)

    def adc200_kkr_default(self):
        print('im here 1')
        self.chan_adc200_ptsofs_1.setValue(590)
        self.chan_adc200_ptsofs_2.setValue(590)
        self.chan_adc200_numpts_1.setValue(424)
        self.chan_adc200_numpts_2.setValue(424)
        self.chan_adc200_timing_1.setValue(0)
        self.chan_adc200_timing_2.setValue(0)
        self.chan_adc200_frq_div_1.setValue(0)
        self.chan_adc200_frq_div_2.setValue(0)
        self.chan_adc200_range_1_1.setValue(1)
        self.chan_adc200_range_1_2.setValue(1)
        self.chan_adc200_range_2_1.setValue(1)
        self.chan_adc200_range_2_2.setValue(1)

    def kkr_sel(self, chan):
        self.ic_mode = chan.val[0]
        self.chan_sel_all.setValue(self.active_tab[self.ic_mode])

    def data_proc(self, chan):
        self.chans_check()
        name = chan.name + self.ic_mode
        if len(self.dict_good_chans[name].val):
            self.dict_temp_chans[name].setValue(chan.val)
            self.expanding_data(self.chan_Tgood_ppn.val[0:76], self.dict_good_chans[name].val[305:381],
                                chan.val[305:381])
            self.correlation(name, self.chan_Tgood_ppn.val[0:76], chan.val[305:381])

    def expanding_data(self, t_data_good, u_data_good, u_data):
        tck = interpolate.splrep(t_data_good, u_data_good, s=0)
        tck1 = interpolate.splrep(t_data_good, u_data, s=0)
        self.ki_time = np.arange(0.0, 375.0, 0.25)
        self.ki_amp_g = interpolate.splev(self.ki_time, tck, der=0)
        self.ki_amp_c = interpolate.splev(self.ki_time, tck1, der=0)

    def correlation(self, name, t_data_good, u_data):
        corr = np.correlate(self.ki_amp_c, self.ki_amp_g, 'same')
        delta_t = (corr.argmax() - (len(corr) / 2)) * self.STEP
        if abs(delta_t) < 20:
            gaussfit = lambda p, x: p[0] * np.exp(-(((x - p[1]) / p[2]) ** 2) / 2) + p[3]  # signal peak and ampl
            errfunc = lambda p, x, y: gaussfit(p, x) - u_data
            p = [0.4, 150, 90, 0]
            p1, success = optimize.leastsq(errfunc, p[:], args=(t_data_good, u_data))

            '''gaussfit = lambda p2, x: p2[0] * np.exp(-(((x - p2[1]) / p2[2]) ** 2) / 2) + p2[3]
            errfunc1 = lambda p2, x, y: gaussfit(p2, x) - u_data_good
            p2 = [0.4, 150, 90, 0]
            p3, success = optimize.leastsq(errfunc1, p2[:], args=(t_data_good, u_data_good))'''

            # if abs(p1[0]) < 0.55:
            #    self.chan_abs_a_good_ppn.setValue(round((p3[0] - p[0]), 6))

            self.dict_t_peak[name].setValue(round(p1[1], 0))
            self.dict_delta_t[name].setValue(round(delta_t, 1))
            self.sigma_proc(delta_t, name)

    def daemon_cmd(self, chan):
        cmd = chan.val
        if cmd:
            cdict = json.loads(cmd)
            if cdict['cmd'] == 'save':
                self.upload_good_chans()
                self.cmd_chan.setValue(json.dumps({'cmd': 'ready'}))
                self.res_chan.setValue(json.dumps({'res': 'good'}))
            if cdict['cmd'] == 'stg_dflt':
                print('im here 0')
                self.adc200_kkr_default()
                self.cmd_chan.setValue(json.dumps({'cmd': 'ready'}))
                self.res_chan.setValue(json.dumps({'res': 'good'}))

    def upload_good_chans(self):
        if self.ic_mode == 'p':
            start = 0
            end = 4
            name = DIR + "good_chan_positron"
            print(os.getcwd())
        else:
            start = 4
            end = 8
            name = DIR + "good_chan_electron"
            print(os.getcwd())
        f = open(name, 'w')
        for i in range(start, end):
            a = self.list_TC[i].val
            self.list_GC[i].setValue(a)
            for j in range(0, 423):
                f.write(str(a[j]))
                f.write("\t")
            f.write("\n")
        # for i in range(start, end):
        #     a = list_DT[i].val
        #     for j in range(0, 200):
        #         f.write(str(a[j]))
        #         f.write("\t")
        #     f.write("\n")
        f.close()

    def chans_check(self):
        check_p = self.chan_Ugood_ppn.val
        check_e = self.chan_Ugood_pen.val
        ic_mode = self.chan_ic_mode.val

        if (check_e.__len__() == 0) or (check_p.__len__() == 0):
            print("here")
            list_GC = self.list_GC
            list_DT = self.list_DT
            self.chan_Tgood_ppn.setValue(self.T)
            self.cmd_chan.setValue(json.dumps({'cmd': 'ready'}))
            self.res_chan.setValue(json.dumps({'res': 'good'}))
            self.chan_n_interp_ppn.setValue(10)
            self.chan_histo_range_ppn.setValue(5)

            d_from_file = np.zeros((423,), dtype=np.double)
            f = open(DIR + "good_chan_electron", "r")
            start = 4
            end = 8
            for j in range(start, end):
                print("write")
                L = f.readline()
                L = L.split()
                for i in range(0, 423):
                    d_from_file[i] = float(L[i])
                list_GC[j].setValue(d_from_file)
            f.close()

            d_from_file = np.zeros((423,), dtype=np.double)
            f = open(DIR + "good_chan_positron", "r")
            start = 0
            end = 4
            for j in range(start, end):
                print("write")
                L = f.readline()
                L = L.split()
                for i in range(0, 423):
                    d_from_file[i] = float(L[i])
                list_GC[j].setValue(d_from_file)
            f.close()

    def sigma_proc(self, delta_t, name):
        hist_range = self.hist_ctrl["cxhw:2.inj.prekick.p.neg.histo_range"]
        bins_num = self.hist_ctrl["cxhw:2.inj.prekick.p.neg.n_interp"]

        delta_t_arr = self.dict_delta_arr[name].val
        if delta_t_arr.__len__() > 99:
            delta_t_arr = np.delete(delta_t_arr, 0)
        delta_t_arr = np.append(delta_t_arr, delta_t)
        sigma1 = np.multiply(delta_t_arr, delta_t_arr)
        sigma = np.sqrt(np.sum(sigma1)/delta_t_arr.__len__())
        self.dict_sigma_t[name].setValue(round(sigma, 1))
        self.dict_delta_arr[name].setValue(delta_t_arr)

        if delta_t_arr.__len__() > 3:
            ppn_y, ppn_x = np.histogram(delta_t_arr, bins=bins_num, range=((-1) * hist_range, hist_range))
            ppn_y_1, ppn_x_1 = np.histogram(delta_t_arr[-3], bins=bins_num,
                                            range=((-1) * hist_range, hist_range))
            ppn_y_2, ppn_x_2 = np.histogram(delta_t_arr[-2], bins=bins_num,
                                            range=((-1) * hist_range, hist_range))
            ppn_y_3, ppn_x_3 = np.histogram(delta_t_arr[-1], bins=bins_num,
                                            range=((-1) * hist_range, hist_range))

            self.dict_hist[name][0].setValue(ppn_x)
            self.dict_hist[name][1].setValue(ppn_y)
            self.dict_hist[name][2].setValue(ppn_x_1)
            self.dict_hist[name][3].setValue(ppn_y_1)
            self.dict_hist[name][4].setValue(ppn_x_2)
            self.dict_hist[name][5].setValue(ppn_y_2)
            self.dict_hist[name][6].setValue(ppn_x_3)
            self.dict_hist[name][7].setValue(ppn_y_3)


class KMService(CXService):
    def main(self):
        print('run main')
        w = KickerApp()

    def clean(self):
        self.log_str('exiting kicker_monitor')

DIR = os.getcwd()
km = KMService("kicker_monitor")
