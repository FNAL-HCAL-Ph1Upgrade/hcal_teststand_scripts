import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import glob
from optparse import OptionParser


def parse_log(log_raw):
        # Create a dictionary, where the key is the section name and the value is a list of lines in the section:
        log_parsed = {}
        sections = log_raw.split("%%")[1:]
        for section in sections:
                lines = section.split("\n")
                log_parsed[lines[0].lower().strip()] = {
                        "registers": {},
                        "lines": [line for line in lines[1:] if line],
                }

        # Format registers into dictionaries:
        for section, values in log_parsed.iteritems():
                for value in values["lines"]:
                        if "->" in value:
                                pieces = value.rpartition(" -> ")
                                values["registers"][pieces[0].strip()] = pieces[2].strip()
        return log_parsed


if __name__ == '__main__':
    
    parser = OptionParser()
    parser.add_option("-d", "--dir", dest="logdir",
                      type="string", default=".",
                      help="Directory containing all the log files"
                      )
    parser.add_option("-o", "--output", dest="output",
		      type="string", default="loginfo",
		      help="name for the output pkl and csv files, do not include the extension here. ")
    
    (options, args) = parser.parse_args()
    

    log_dirs = glob.glob("{0}/18*".format(options.logdir)) #Change to correct year if necessary
    
    charm_data = []

    for log_dir in log_dirs:
        logs = glob.glob("{0}/*.log".format(log_dir))
        
        for log in logs:
            if "prbs" in log:

                continue
            with open(log) as f:
                charm_log = {}

                # Get time
                charm_log["time"] = log.split("/")[-1].replace(".log","")

                # Get all registers
                log_parsed = parse_log(f.read())
                # -- temperatures --
                charm_log["SiPM_temperature"] = log_parsed["temperatures"]["lines"][1].split()[-1]
                for i in [1,2]:
			for ii in [1,2,3,4]:
				form = ii+((i-1)*4)
                    		charm_log["RM_card{0}_temperature".format(form)] = log_parsed["registers"]["registers"]["get HB1-{0}-{1}-B_SHT_temp_f".format(i,ii)]
                try:
                    charm_log["CU_temperature"] = log_parsed["registers"]["registers"]["get HB1-calib-B_SHT_temp_f"]
                except:
                    charm_log["CU_temperature"] = None
                # -- voltages and currents -- 
		charm_log["Vin_Voltage_J16"] = log_parsed["voltages"]["lines"][4].split()[-1]
		charm_log["Vin_Voltage_J15"] = log_parsed["voltages"]["lines"][5].split()[-1]
		charm_log["Vin_Voltage_J14"] = log_parsed["voltages"]["lines"][6].split()[-1]
		try:
                	charm_log["BiasSupplyV"] = log_parsed["biasvoltage"]["registers"]["BiasSupplyVoltage"]
                	charm_log["BiasSupplyC"] = log_parsed["biasvoltage"]["registers"]["BiasSupplyCurrent"]	
		except:
			charm_log["BiasSupplyV"] = None
			charm_log["BiasSupplyC"] = None
		'''
                charm_log["PS_voltage"] = log_parsed["power"]["lines"][0].split()[1]
                charm_log["PS_current"] = log_parsed["power"]["lines"][1].split()[1]
                charm_log["Bkp_voltage_J13"] = log_parsed["power"]["lines"][2].split()[-1]
                charm_log["Bkp_voltage_J14"] = log_parsed["power"]["lines"][3].split()[-1]
                charm_log["Bkp_voltage_J15"] = log_parsed["power"]["lines"][4].split()[-1]
                charm_log["Bkp_voltage_J16"] = log_parsed["power"]["lines"][5].split()[-1]
                charm_log["Bkp_current_J13"] = log_parsed["power"]["lines"][6].split()[-1]
                charm_log["Bkp_current_J14"] = log_parsed["power"]["lines"][7].split()[-1]
                charm_log["Bkp_current_J15"] = log_parsed["power"]["lines"][8].split()[-1]
                charm_log["Bkp_current_J16"] = log_parsed["power"]["lines"][9].split()[-1]
		'''
                charm_log["PeltierVoltage"] = log_parsed["registers"]["registers"]["get HB{0}-{1}-PeltierVoltage_f".format(1,2)]
                charm_log["PeltierCurrent"] = log_parsed["registers"]["registers"]["get HB{0}-{1}-PeltierCurrent_f".format(1,2)]
                charm_log["BVin"] = log_parsed["registers"]["registers"]["get HB{0}-{1}-BVin_f".format(1,2)]
                charm_data.append(charm_log)

    # make dataframe
    df = pd.DataFrame(charm_data)
    df["time"] = pd.to_datetime(df["time"], format="%y%m%d_%H%M%S")
    df = df.set_index('time')
    df = df.apply(pd.to_numeric, errors='coerce')
    #df = pd.to_numeric(df, errors="coerce")
    #print df

    # make the output files
    df.to_pickle("{0}.pkl".format(options.output))
    df.to_csv("{0}.csv".format(options.output))

