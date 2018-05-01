import pycx4.qcda as cda

chan_fit_switch = cda.StrChan("cxhw:2.e_diss" + ".fit_switch", max_nelems=1024)
chan_fit_switch.setValue('gauss')
print(chan_fit_switch.val, 'd')
