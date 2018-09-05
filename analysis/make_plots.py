import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
from datetime import datetime

from optparse import OptionParser
import sys




if __name__ == "__main__":
    power_cycles = [
                "2018-08-29 13:44:07.473202",
                "2018-08-29 23:58:02.029136",
                "2018-08-29 23:58:56.375937",
                "2018-08-30 00:04:18.729628",
                "2018-08-30 09:59:05.054036",
                "2018-08-30 17:45:15.129030",
                "2018-09-02 17:02:31.759043",
                "2018-09-02 22:30:00.000000",
                "2018-09-02 23:12:45.205361",
                "2018-09-02 23:25:35.855088",
                "2018-09-03 08:56:33.679489"]

    bkp_cycles = [
                "2018-08-29 23:23:15",
                "2018-08-30 09:54:18",
                "2018-08-30 21:25:34",
                "2018-08-31 11:27:00",
                "2018-09-02 16:46:00",
                "2018-09-03 09:12:00",
                "2018-09-03 13:30:28"]
        
    auto_reset = [
                "2018-08-30 21:25:34",
                "2018-08-31 19:20:45",
                "2018-09-01 16:10:53",
                "2018-09-02 00:54:29",
                "2018-09-02 21:31:21",
                "2018-09-02 21:34:50",
                "2018-09-02 21:36:21",
                "2018-09-02 21:46:22",
                "2018-09-02 21:49:50",
                "2018-09-02 21:51:22",
                "2018-09-02 21:56:22",
                "2018-09-02 22:01:23",
                "2018-09-02 22:04:51",
                "2018-09-02 22:06:23",
                "2018-09-02 22:11:23",
                "2018-09-02 22:16:24",
                "2018-09-02 22:19:52",
                "2018-09-02 22:21:25",
                "2018-09-02 22:26:26",
                "2018-09-02 23:28:11",
                "2018-09-03 13:07:36",
                "2018-09-03 13:12:36",
                "2018-09-03 13:15:28",
                "2018-09-03 13:17:36",
                "2018-09-03 13:22:37",
                "2018-09-03 13:27:37",
                "2018-09-03 13:30:28"]

    power = None
    bkp = None
    auto = None
    for idx,date in enumerate(auto_reset):
        auto_reset[idx] = datetime(int(date[:4]),int(date[5:7]),int(date[8:10]),int(date[11:13]),int(date[14:16]),int(date[17:19]))
        auto = plt.axvline(auto_reset[idx], label='auto reset', color ='g', linestyle="--", linewidth=.5)
    for idx,date in enumerate(power_cycles):
        power_cycles[idx] = datetime(int(date[:4]),int(date[5:7]),int(date[8:10]),int(date[11:13]),int(date[14:16]),int(date[17:19]))
        power = plt.axvline(power_cycles[idx], label='power cycles', color ='r', linestyle="--", linewidth=.5)
    for idx,date in enumerate(bkp_cycles):
        bkp_cycles[idx] = datetime(int(date[:4]),int(date[5:7]),int(date[8:10]),int(date[11:13]),int(date[14:16]),int(date[17:19]))
        bkp = plt.axvline(bkp_cycles[idx], label='bkp cycles', color ='#ffa500', linestyle="--", linewidth=.5)
	 
    def lines():   	
    	for idx,date in enumerate(auto_reset):
        	auto = plt.axvline(auto_reset[idx], label='auto reset', color ='g', linestyle="--", linewidth=.5)
    	for idx,date in enumerate(power_cycles):
        	power = plt.axvline(power_cycles[idx], label='power cycles', color ='r', linestyle="--", linewidth=.5)
    	for idx,date in enumerate(bkp_cycles):
        	bkp = plt.axvline(bkp_cycles[idx], label='bkp cycles', color ='#ffa500', linestyle="--", linewidth=.5)
    parser = OptionParser()
    parser.add_option("-i", "--input", dest="input",
		      type="string", default="loginfo",
		      help="name for the input pkl files, do not include the extension here. ")
    
    (options, args) = parser.parse_args()

    # read the input file
    try:
        df = pd.read_pickle("{0}.pkl".format(options.input))
    except IOError:
        print "Didn't find a file called {0}.pkl".format(options.input)
        sys.exit()

    # make some plots
    fig = plt.figure()
    fig_size = plt.rcParams["figure.figsize"]
    fig_size[0] = 12
    fig_size[1] = 6
    plt.rcParams["figure.figsize"] = fig_size

    ax = df.plot(y=["RM_card1_temperature","RM_card2_temperature","RM_card3_temperature","RM_card4_temperature","RM_card5_temperature","RM_card6_temperature","RM_card7_temperature","RM_card8_temperature","CU_temperature"], ylim=(24,50))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    ax.set_xlabel("")
    lines()
    plt.legend( (power,bkp,auto),("Power","Bkp","Auto"),loc = 2)
    plt.savefig("RM_temperature.pdf")
    plt.savefig("RM_temperature.png")
    plt.clf()

    ax = df.plot(y=["SiPM_temperature","PeltierVoltage", "PeltierCurrent"], secondary_y=["PeltierVoltage", "PeltierCurrent"], ylim=(8,29))
    ax.right_ax.set_ylim(-0.2,3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    ax.set_xlabel("")
    lines()
    plt.legend( (power,bkp,auto),("Power","Bkp","Auto"),loc = 2)
    plt.savefig("SiPM.pdf")
    plt.savefig("SiPM.png")
    plt.clf()

    ax = df.plot(y=["VIN_CLK","1V2_aCTRL","1V2_bCTRL","2V5_CLK","3V3_BKP_CLK","3V3_BKP_aCTRL","3V3_BKP_bCTRL","3V3_CLK"])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    ax.set_xlabel("")
    lines()
    plt.legend( (power,bkp,auto),("Power","Bkp","Auto"),loc = 2)
    plt.savefig("CCM_Currents.pdf")
    plt.savefig("CCM_Currents.png")
    plt.clf()

    ax = df.plot(y=["BiasSupplyV","BiasSupplyC"], secondary_y=["BiasSupplyC"],)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    ax.set_xlabel("")
    ax.get_yaxis().get_major_formatter().set_useOffset(False)
    ax.set_ylabel("Volts")
    lines()
    plt.legend( (power,bkp,auto),("Power","Bkp","Auto"),loc = 2)
    plt.savefig("Bias.pdf")
    plt.savefig("Bias.png")
    plt.clf()

    #ax = df.plot(y=["PS_voltage", "Bkp_voltage_J13", "Bkp_voltage_J14", "Bkp_voltage_J15", "Bkp_voltage_J16", "BVin"], secondary_y="BVin", ylim=(7.0,13))
    ax = df.plot(y=["Vin_Voltage_J16","Vin_Voltage_J15","Vin_Voltage_J14","BVin"], secondary_y="BVin", ylim=(7.0,13))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    ax.right_ax.set_ylim(40,170)
    ax.set_xlabel("")
    lines()
    plt.legend( (power,bkp,auto),("Power","Bkp","Auto"),loc = 2)
    plt.savefig("voltages.pdf")
    plt.savefig("voltages.png")
    plt.clf()

    #ax = df.plot(y=["PS_current","Bkp_current_J13", "Bkp_current_J14", "Bkp_current_J15", "Bkp_current_J16"], 
    #             secondary_y=["Bkp_current_J13", "Bkp_current_J14", "Bkp_current_J15", "Bkp_current_J16"],
    #             ylim=(0,20))
    ax = df.plot(y=["Vin_Voltage_J16","Vin_Voltage_J15","Vin_Voltage_J14"], secondary_y=["Vin_Voltage_J16","Vin_Voltage_J15","Vin_Voltage_J14"], ylim=(0,20))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    #ax.right_ax.set_ylim(-0.2,3)
    ax.set_xlabel("")
    lines()
    plt.legend( (power,bkp,auto),("Power","Bkp","Auto"),loc = 2)
    plt.savefig("currents.pdf")
    plt.savefig("currents.png")
    plt.clf()


    ax = df.plot(y=["QieDLLNoLock_%i_%i_Bot"%(i, j) for i in xrange(1,3) for j in xrange(1,5)] + ["QieDLLNoLock_%i_%i_Top"%(i, j) for i in xrange(1,3) for j in xrange(1,5)])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    #ax.right_ax.set_ylim(-0.2,3)
    ax.set_xlabel("")
    lines()
    plt.legend( (power,bkp,auto),("Power","Bkp","Auto"),loc = 2)
    plt.legend(loc=9, ncol=3)
    plt.savefig("QIEDLLNoLock.pdf")
    plt.savefig("QIEDLLNoLock.png")
    plt.clf()
