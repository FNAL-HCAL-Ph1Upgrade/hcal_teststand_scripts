#import hcal_teststand.hcal_teststand as hc
from hcal_teststand.simpleTestStand import teststand
import os, sys
from optparse import OptionParser
import hcal_teststand.uhtr as uhtr
import hcal_teststand.ngfec as ngfec

def HEsetup(ts, section="all"):
        log = []

        biasVoltages = {1:[
        "put HB1-1-biasvoltage6_f 65.7225010839724",
        "put HB1-1-biasvoltage5_f 65.7918014310248",
        "put HB1-1-biasvoltage16_f 65.4634813040158",
        "put HB1-1-biasvoltage15_f 65.7813362201465",
        "put HB1-1-biasvoltage12_f 65.5476381772413",
        "put HB1-1-biasvoltage11_f 65.6100089170712",
        "put HB1-1-biasvoltage2_f 65.9724077943273",
        "put HB1-1-biasvoltage1_f 65.6153463393655",
        "put HB1-1-biasvoltage8_f 65.747880807253",
        "put HB1-1-biasvoltage7_f 66.1089344166096",
        "put HB1-1-biasvoltage14_f 65.6686884254598",
        "put HB1-1-biasvoltage13_f 65.5148623489631",
        "put HB1-1-biasvoltage10_f 65.910155593707",
        "put HB1-1-biasvoltage9_f 65.8152627607403",
        "put HB1-1-biasvoltage4_f 65.7404494521326",
        "put HB1-1-biasvoltage3_f 65.7914104327441",
        "put HB1-1-biasvoltage22_f 65.7109053417481",
        "put HB1-1-biasvoltage21_f 66.1126926265756",
        "put HB1-1-biasvoltage32_f 65.9293754660753",
        "put HB1-1-biasvoltage31_f 65.9535015232308",
        "put HB1-1-biasvoltage28_f 65.8562630170035",
        "put HB1-1-biasvoltage27_f 65.6134667234691",
        "put HB1-1-biasvoltage18_f 65.9841554967006",
        "put HB1-1-biasvoltage17_f 65.8949685830519",
        "put HB1-1-biasvoltage24_f 65.7997327206157",
        "put HB1-1-biasvoltage23_f 65.8239569888164",
        "put HB1-1-biasvoltage30_f 65.6363429495769",
        "put HB1-1-biasvoltage29_f 65.8216931799362",
        "put HB1-1-biasvoltage26_f 65.8542022309516",
        "put HB1-1-biasvoltage25_f 65.9102706416723",
        "put HB1-1-biasvoltage20_f 65.9045731094859",
        "put HB1-1-biasvoltage19_f 65.8656406166701",
        "put HB1-1-biasvoltage38_f 65.6900145004334",
        "put HB1-1-biasvoltage37_f 65.9142237610625",
        "put HB1-1-biasvoltage48_f 65.6112476183334",
        "put HB1-1-biasvoltage47_f 65.666707695799",
        "put HB1-1-biasvoltage44_f 65.7407703684707",
        "put HB1-1-biasvoltage43_f 65.8674303727125",
        "put HB1-1-biasvoltage34_f 66.0055432192393",
        "put HB1-1-biasvoltage33_f 65.6742376356111",
        "put HB1-1-biasvoltage40_f 65.7800291290937",
        "put HB1-1-biasvoltage39_f 66.0731620652416",
        "put HB1-1-biasvoltage46_f 65.9427787897791",
        "put HB1-1-biasvoltage45_f 65.9122013853261",
        "put HB1-1-biasvoltage42_f 65.817959123236",
        "put HB1-1-biasvoltage41_f 65.6650202693258",
        "put HB1-1-biasvoltage36_f 65.6655265443412",
        "put HB1-1-biasvoltage35_f 65.9118856485928",
        "put HB1-1-biasvoltage54_f 65.7010638953009",
        "put HB1-1-biasvoltage53_f 65.8210381648958",
        "put HB1-1-biasvoltage64_f 65.6766948804934",
        "put HB1-1-biasvoltage63_f 65.8061992633123",
        "put HB1-1-biasvoltage60_f 65.6299967106654",
        "put HB1-1-biasvoltage59_f 65.83846305912",
        "put HB1-1-biasvoltage50_f 65.5606168198508",
        "put HB1-1-biasvoltage49_f 65.4508817827916",
        "put HB1-1-biasvoltage56_f 65.8071980135287",
        "put HB1-1-biasvoltage55_f 65.770705124797",
        "put HB1-1-biasvoltage62_f 65.9281330097055",
        "put HB1-1-biasvoltage61_f 65.7050268254943",
        "put HB1-1-biasvoltage58_f 65.4159177733417",
        "put HB1-1-biasvoltage57_f 65.6732896520018",
        "put HB1-1-biasvoltage52_f 65.4453092294579",
        "put HB1-1-biasvoltage51_f 65.8552451091451",
        ],
        2:[
        "put HB1-2-biasvoltage6_f 66.5874771379579",
        "put HB1-2-biasvoltage5_f 66.4489525639337",
        "put HB1-2-biasvoltage16_f 66.7315497681976",
        "put HB1-2-biasvoltage15_f 66.5049971774728",
        "put HB1-2-biasvoltage12_f 66.2828531845272",
        "put HB1-2-biasvoltage11_f 66.3368510246479",
        "put HB1-2-biasvoltage2_f 66.5027080176426",
        "put HB1-2-biasvoltage1_f 66.356969718817",
        "put HB1-2-biasvoltage8_f 66.463332392334",
        "put HB1-2-biasvoltage7_f 66.3037261059952",
        "put HB1-2-biasvoltage14_f 66.4836352898261",
        "put HB1-2-biasvoltage13_f 66.7178601025517",
        "put HB1-2-biasvoltage10_f 66.5833204072806",
        "put HB1-2-biasvoltage9_f 66.4840149065641",
        "put HB1-2-biasvoltage4_f 66.4437057746086",
        "put HB1-2-biasvoltage3_f 66.4883021278543",
        "put HB1-2-biasvoltage22_f 66.4232240396788",
        "put HB1-2-biasvoltage21_f 66.6902026486364",
        "put HB1-2-biasvoltage32_f 66.445705734921",
        "put HB1-2-biasvoltage31_f 66.6021057024887",
        "put HB1-2-biasvoltage28_f 66.6888314786244",
        "put HB1-2-biasvoltage27_f 66.4644315283965",
        "put HB1-2-biasvoltage18_f 66.6123959602192",
        "put HB1-2-biasvoltage17_f 66.6115336891636",
        "put HB1-2-biasvoltage24_f 66.1518140740958",
        "put HB1-2-biasvoltage23_f 66.2296562265076",
        "put HB1-2-biasvoltage30_f 66.0597002089902",
        "put HB1-2-biasvoltage29_f 66.1271481012956",
        "put HB1-2-biasvoltage26_f 66.3047833906933",
        "put HB1-2-biasvoltage25_f 66.2515576016026",
        "put HB1-2-biasvoltage20_f 66.1933138952049",
        "put HB1-2-biasvoltage19_f 66.1449436404464",
        "put HB1-2-biasvoltage38_f 66.1892519770007",
        "put HB1-2-biasvoltage37_f 66.2199984052705",
        "put HB1-2-biasvoltage48_f 66.1297295614064",
        "put HB1-2-biasvoltage47_f 66.2079264946608",
        "put HB1-2-biasvoltage44_f 66.0381699268743",
        "put HB1-2-biasvoltage43_f 66.1250394769835",
        "put HB1-2-biasvoltage34_f 66.343440582423",
        "put HB1-2-biasvoltage33_f 66.1832864199507",
        "put HB1-2-biasvoltage40_f 65.9148691234405",
        "put HB1-2-biasvoltage39_f 66.0466013401936",
        "put HB1-2-biasvoltage46_f 66.122157645739",
        "put HB1-2-biasvoltage45_f 66.1671931351723",
        "put HB1-2-biasvoltage42_f 65.8763253192436",
        "put HB1-2-biasvoltage41_f 65.9297527878843",
        "put HB1-2-biasvoltage36_f 66.157123153089",
        "put HB1-2-biasvoltage35_f 66.2421433999091",
        "put HB1-2-biasvoltage54_f 66.1938255391638",
        "put HB1-2-biasvoltage53_f 66.0454234142195",
        "put HB1-2-biasvoltage64_f 66.3027836678119",
        "put HB1-2-biasvoltage63_f 66.0914002790416",
        "put HB1-2-biasvoltage60_f 66.1238570525794",
        "put HB1-2-biasvoltage59_f 65.9230879854262",
        "put HB1-2-biasvoltage50_f 66.4001261912566",
        "put HB1-2-biasvoltage49_f 65.9690829681341",
        "put HB1-2-biasvoltage56_f 66.1612923919406",
        "put HB1-2-biasvoltage55_f 65.7890172265987",
        "put HB1-2-biasvoltage62_f 66.1034409052421",
        "put HB1-2-biasvoltage61_f 66.1212693883942",
        "put HB1-2-biasvoltage58_f 66.0760702883681",
        "put HB1-2-biasvoltage57_f 65.8636283114072",
        "put HB1-2-biasvoltage52_f 65.9230721727946",
        "put HB1-2-biasvoltage51_f 65.8018569792357",
        ]
        }
        
	# loop over the crates and slots
	for icrate, crate in enumerate(ts.fe_crates):
		for slot in ts.qie_slots[icrate]:
			print "crate", crate, "slot", slot
			cmds1 = ["put {0}-{1}-dac1-daccontrol_RefSelect 0".format(crate, slot),
				 "put {0}-{1}-dac1-daccontrol_ChannelMonitorEnable 1".format(crate, slot), 
				 "put {0}-{1}-dac1-daccontrol_InternalRefEnable 1".format(crate, slot),
				 "put {0}-{1}-dac2-daccontrol_RefSelect 0".format(crate, slot),
				 "put {0}-{1}-dac2-daccontrol_ChannelMonitorEnable 1".format(crate, slot), 
				 "put {0}-{1}-dac2-daccontrol_InternalRefEnable 1".format(crate, slot),
				 "put {0}-{1}-dac1-monchan 0x3f".format(crate, slot),
				 "put {0}-{1}-dac2-monchan 0x3f".format(crate, slot),
				 "put {0}-{1}-muxchannel 1".format(crate, slot)
				 ]

			cmds2 = biasVoltages[slot]
                        
			cmds3 = [#"put {0}-{1}-peltier_stepseconds 900".format(crate, slot),
                                "put {0}-{1}-peltier_targettemperature_f 20.0".format(crate, slot),
                                #"put {0}-{1}-peltier_adjustment_f 0.25".format(crate, slot),
                                "put {0}-{1}-peltier_control 1".format(crate, slot),
                                "put {0}-{1}-peltier_enable 1".format(crate, slot),
                                #"put {0}-{1}-SetPeltierVoltage_f 1.".format(crate, slot)
                                ]
                        
#                        output = ngfec.send_commands(port=ts.port, cmds=cmds1, script=True)
#                        log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])


                        if section == "all" or section == "bias":
                                output = ngfec.send_commands(port=ts.port, cmds=cmds2, script=True)
                                log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])

                        output = ngfec.send_commands(port=ts.port, cmds=cmds3, script=True)
                        log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
			
			for qiecard in ts.qiecards[crate][slot]:
				cmds4 = ["put {0}-{1}-{2}-iTop_scratch 0xab".format(crate, slot, qiecard),
                                         "put {0}-{1}-{2}-iBot_scratch 0xab".format(crate, slot, qiecard),
					 "put {0}-{1}-{2}-B_SCRATCH 0xab".format(crate, slot, qiecard)
					 ]
                                if section == "all" or section == "scratch":
                                    output = ngfec.send_commands(port=ts.port, cmds=cmds4, script=True)
                                    log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])
				    


		# for ngccm, write scratch
		cmds5 = ["put {0}a-mezz_scratch 0xf".format(crate)]
		if section == "all" or section == "scratch":
			output = ngfec.send_commands(port=ts.port, cmds=cmds5)
			log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])

		# for CU, write scratch
#		cmds6 = ["put {0}-calib-iTop_scratch 0xab".format(crate),
#                         "put {0}-calib-iBot_scratch 0xab".format(crate),
#			 "put {0}-calib-B_SCRATCH 0xab".format(crate)]
#		if section == "all" or section == "scratch":
#			output = ngfec.send_commands(port=ts.port, cmds=cmds6)
#			log.extend(["{0} -> {1}\n".format(result["cmd"], result["result"]) for result in output])

	print "".join(log)

def HEreset(ts):
	for crate in ts.fe_crates:
		cmds1 = ["put {0}a-bkp_reset 1".format(crate),
			 "wait",
			 "wait",
			 "wait",
			 "wait",
			 "put {0}a-bkp_reset 0".format(crate)]
		output = ngfec.send_commands(port=ts.port, cmds=cmds1, script=True)
		for out in output:
			print "{0} -> {1}".format(out["cmd"], out["result"])

def HEtogglebkp_pwr(ts): 
	for crate in ts.fe_crates:
		cmds1 = ["put {0}a-bkp_pwr_enable 0".format(crate),
			 "wait",
			 "wait",
			 "wait",
			 "wait",
			 "put {0}a-bkp_pwr_enable 1".format(crate)]
		output = ngfec.send_commands(port=ts.port, cmds=cmds1, script=True)
		for out in output:
			print "{0} -> {1}".format(out["cmd"], out["result"])

def HEbkp_pwr_off(ts): 
	for crate in ts.fe_crates:
		cmds1 = ["put {0}a-bkp_pwr_enable 0".format(crate),]
		output = ngfec.send_commands(port=ts.port, cmds=cmds1, script=True)
		for out in output:
			print "{0} -> {1}".format(out["cmd"], out["result"])


def HBLinks(ts):
        uhtr.initLinks(ts, OrbitDelay=322, Auto_Realign=0, OnTheFlyAlignment=0, CDRreset=0, 
                       GTXreset=0, verbose=True)


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("--powerOff", dest="powerOff",
                      default=False, action='store_true',
                      help="Disable and Enable backplane power (RM and CU)",
                      )
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

#    if not options.tstype:
#        print "Please specify which teststand to use!"
#        sys.exit()
#    tstype = options.tstype

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

    #ts = hc.teststand(tstype)
    ts = teststand()

    if options.powerOff:
        HEbkp_pwr_off(ts)
        exit(0)

    if togglePower:
        HEtogglebkp_pwr(ts)

    if reset:
        HEreset(ts)

    if setup:
        HEsetup(ts)

    if link:
        HBLinks(ts)
