import hcal_teststand.hcal_teststand as hc
import os, sys
from optparse import OptionParser
import hcal_teststand.uhtr as uhtr
import hcal_teststand.ngfec as ngfec

def HEsetup(ts, section="all"):
        log = []

	# loop over the crates and slots
	for icrate, crate in enumerate(ts.fe_crates):
		for slot in ts.qie_slots[icrate]:
			print "crate", crate, "slot", slot
			cmds1 = ["put HE{0}-{1}-dac1-daccontrol_RefSelect 0".format(crate, slot),
				 "put HE{0}-{1}-dac1-daccontrol_ChannelMonitorEnable 1".format(crate, slot), 
				 "put HE{0}-{1}-dac1-daccontrol_InternalRefEnable 1".format(crate, slot),
				 "put HE{0}-{1}-dac2-daccontrol_RefSelect 0".format(crate, slot),
				 "put HE{0}-{1}-dac2-daccontrol_ChannelMonitorEnable 1".format(crate, slot), 
				 "put HE{0}-{1}-dac2-daccontrol_InternalRefEnable 1".format(crate, slot),
				 "put HE{0}-{1}-dac1-monchan 0x3f".format(crate, slot),
				 "put HE{0}-{1}-dac2-monchan 0x3f".format(crate, slot),
				 "put HE{0}-{1}-muxchannel 1".format(crate, slot)
				 ]

			cmds2 = ["put HE{0}-{1}-biasvoltage[1-48]_f 48*69.0".format(crate, slot)]

			cmds3 = ["put HE{0}-{1}-peltier_stepseconds 900".format(crate, slot),
				 "put HE{0}-{1}-peltier_targettemperature_f 20.0".format(crate, slot),
				 "put HE{0}-{1}-peltier_adjustment_f 0.25".format(crate, slot),
				 "put HE{0}-{1}-peltier_control 1".format(crate, slot),
				 "put HE{0}-{1}-peltier_enable 1".format(crate, slot),
				 "put HE{0}-{1}-SetPeltierVoltage_f 1.".format(crate, slot)
				 ]

			if ts.name != "HEoven":
                                if section == "all" or section == "bias":
                                    output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
                                    log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
                                    output = ngfec.send_commands(ts=ts, cmds=cmds2, script=True)
                                    log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
                                if section == "all" or section == "peltier":
                                    output = ngfec.send_commands(ts=ts, cmds=cmds3, script=True)
                                    log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
			
			for qiecard in ts.qiecards[crate, slot]:
				cmds4 = ["put HE{0}-{1}-{2}-i_scratch 0xab".format(crate, slot, qiecard),
					 "put HE{0}-{1}-{2}-B_SCRATCH 0xab".format(crate, slot, qiecard)
					 ]
                                if section == "all" or section == "scratch":
                                    output = ngfec.send_commands(ts=ts, cmds=cmds4, script=True)
                                    log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
				    
		# for ngccm, write scratch
		cmds5 = ["put HE{0}-mezz_scratch 0xf 0xf 0xf 0xf".format(crate)]
		if section == "all" or section == "scratch":
			output = ngfec.send_commands(ts=ts, cmds=cmds5)
			log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])

	print "".join(log)

def HEreset(ts):
	for crate in ts.fe_crates:
		cmds1 = ["put HE{0}-bkp_reset 1".format(crate),
			 "wait",
			 "wait",
			 "wait",
			 "wait",
			 "put HE{0}-bkp_reset 0".format(crate)]
		output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
		for out in output:
			print "{0} -> {1}".format(out["cmd"], out["result"])

def HEtogglebkp_pwr(ts): 
	for crate in ts.fe_crates:
		cmds1 = ["put HE{0}-bkp_pwr_enable 0".format(crate),
			 "wait",
			 "wait",
			 "wait",
			 "wait",
			 "put HE{0}-bkp_pwr_enable 1".format(crate)]
		output = ngfec.send_commands(ts=ts, cmds=cmds1, script=True)
		for out in output:
			print "{0} -> {1}".format(out["cmd"], out["result"])


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("--togglePower", dest="togglePower",
                      default=False, action='store_true',
                      help="Disable and Enable backplane power (RM and CU)",
                      )
    parser.add_option("--reset", dest="reset",
                      default=False, action='store_true',
                      help="Do reset",
                      )
    parser.add_option("--setup", dest="setup",
                      default=False, action='store_true',
                      help="Reconfigure the front end using ccmserver",
                      )
    parser.add_option("--link", dest="link",
                      default=False, action='store_true',
                      help="Do link initialization",
                      )
    parser.add_option("--all", dest="all",
                      default=False, action='store_true',
                      help="Do all initializations",
                      )
    parser.add_option("-t", "--teststand", dest="tstype",
                      type="string",
                      help="Which teststand to set up?"
                      )

    (options, args) = parser.parse_args()

    if not options.tstype:
        print "Please specify which teststand to use!"
        sys.exit()
    tstype = options.tstype

    togglePower = False
    reset = False
    setup = False
    link = False
    if options.all:
        togglePower = True
        reset = True
        setup = True
        link = True

    if options.togglePower:
        togglePower = True
    if options.reset:
        reset = True
    if options.setup:
        setup = True
    if options.link:
        link = True

    ts = hc.teststand(tstype)

    if togglePower:
        HEtogglebkp_pwr(ts)

    if reset:
        HEreset(ts)

    if link and tstype != "HEoven":
        # initialize the links
        uhtr.initLinks(ts, OrbitDelay=53, Auto_Realign=1, OnTheFlyAlignment=0, CDRreset=1, GTXreset=1, verbose=True)
        print uhtr.linkStatus(ts)

    if setup:
        HEsetup(ts)

