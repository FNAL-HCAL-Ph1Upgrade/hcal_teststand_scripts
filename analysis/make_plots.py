import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from optparse import OptionParser
import sys



if __name__ == "__main__":
    

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

    ax = df.plot(y=["RM_card1_temperature","RM_card2_temperature", "RM_card4_temperature", "CU_temperature"], ylim=(24,33))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    ax.set_xlabel("")
    plt.savefig("RM_temperature.pdf")
    plt.savefig("RM_temperature.png")
    plt.clf()

    ax = df.plot(y=["SiPM_temperature","PeltierVoltage", "PeltierCurrent"], secondary_y=["PeltierVoltage", "PeltierCurrent"], ylim=(8,29))
    ax.right_ax.set_ylim(-0.2,3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    ax.set_xlabel("")
    plt.savefig("SiPM.pdf")
    plt.savefig("SiPM.png")
    plt.clf()

    ax = df.plot(y=["PS_voltage", "Bkp_voltage_J13", "Bkp_voltage_J14", "Bkp_voltage_J15", "Bkp_voltage_J16", "BVin"], secondary_y="BVin", ylim=(8.5,13))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    ax.right_ax.set_ylim(40,170)
    ax.set_xlabel("")
    plt.savefig("voltages.pdf")
    plt.savefig("voltages.png")
    plt.clf()

    ax = df.plot(y=["PS_current","Bkp_current_J13", "Bkp_current_J14", "Bkp_current_J15", "Bkp_current_J16"], 
                 secondary_y=["Bkp_current_J13", "Bkp_current_J14", "Bkp_current_J15", "Bkp_current_J16"],
                 ylim=(0,20))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    ax.right_ax.set_ylim(-0.2,3)
    ax.set_xlabel("")
    plt.savefig("currents.pdf")
    plt.savefig("currents.png")
    plt.clf()