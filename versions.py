####################################################################
# Type: SCRIPT                                                     #
#                                                                  #
# Description: This script prints out version information for all  #
# of the components in a teststand.                                #
####################################################################

from hcal_teststand import *
from hcal_teststand.hcal_teststand import *
import sys

# FUNCTIONS:
def print_amc13_info(ts):		# Fetches and prints AMC13 version information.
	amc_info = amc13.get_info(ts=ts)
	print "* AMC13  ================================="
	if (amc_info["sn"] == -1):
		print "\tERROR: There was a problem fetching the AMC13 information."
		print "\tThe log is below:\n++++++++++++++ LOG ++++++++++++++++++\n{0}\n+++++++++++++ /LOG ++++++++++++++++++".format(amc_info["log"])
	else:
		print "\tSN: {0}".format(amc_info["sn"])
		print "\tFW version (T1): {0:04d}".format(amc_info["version_fw"][0])
		print "\tFW version (T2): {0:04d}".format(amc_info["version_fw"][1])
		print "\tSW version: {0}".format(amc_info["version_sw"])
		print "\tNotes: \"Tx\" stands for \"Tongue x\", different boards in the AMC13. Only T1 and T2 talk to the BE backplane."
#		print "\tLog: {0}".format(amc_info["log"])

def print_glib_info(ts):
	glib_info = glib.get_info(ts)
	print "* GLIB   ================================="
	if (glib_info["version_fw"] == "000000"):
		print "\tERROR: There was a problem fetching the GLIB information."
		print "\tThe log is below:\n++++++++++++++ LOG ++++++++++++++++++\n{0}\n+++++++++++++ /LOG ++++++++++++++++++".format(glib_info["log"])
	else:
		print "\tFW version: {0}".format(glib_info["version_fw"])

def print_uhtr_info(ts):
	uhtr_infos = uhtr.get_info(ts)
	for uhtr_info in uhtr_infos:
		print "* uHTR (Slot {0:02d}) =========================".format(uhtr_info["slot"])
		print "\tFW version (front): {0}".format(uhtr_info["version_fw_front_str"])
		print "\tFW type (front): {0} ({1})".format(uhtr_info["version_fw_type_front"][0], uhtr_info["version_fw_type_front"][1])
		print "\tFW version (back): {0}".format(uhtr_info["version_fw_back_str"])
		print "\tFW type (back): {0} ({1})".format(uhtr_info["version_fw_type_back"][0], uhtr_info["version_fw_type_back"][1])
		print "\tSW version: ? (it's not currently possible to find out)"

def print_ngccm_info(ts):
	ngccm_info = ngccm.get_info(ts, ts.fe_crates[0])
	print "* ngCCM  ================================="
	if (ngccm_info["version_fw_mez_major"] == -1):
		print "\tERROR: There was a problem fetching the ngCCM information."
		print "\tThe log is below:\n++++++++++++++ LOG ++++++++++++++++++\n{0}\n+++++++++++++ /LOG ++++++++++++++++++".format(ngccm_info["log"])
	else:
		print "\tFW version (mezzanine): {0}".format(ngccm_info["version_fw_mez"])
		print "\tSW version: {0}".format(ngccm_info["version_sw"])

def print_bridge_info(ts, crate, slot):
	bridge_info = qie.get_bridge_info(ts, crate, slot)
	print "* BRIDGE (Crate {0}, Slot {1}) ===============".format(crate, slot)
	if (bridge_info["version_fw"] == "00.00.0000"):
		print "\tERROR: There was a problem fetching the BRIDGE information."
		print "\tThe log is below:\n++++++++++++++ LOG ++++++++++++++++++\n{0}\n+++++++++++++ /LOG ++++++++++++++++++".format(bridge_info["log"])
	else:
		print "\tFW version: {0}".format(bridge_info["version_fw"])

def print_igloo_info(ts, crate, slot):
	igloo_info = qie.get_igloo_info(ts, crate, slot)
	print "* IGLOO  (Crate {0}, Slot {1}) ===============".format(crate, slot)
	if (igloo_info["version_fw_top"] == "00.00"):
		print "\tERROR: There was a problem fetching the IGLOO's top FPGA information."
		print "\tThe log is below:\n++++++++++++++ LOG ++++++++++++++++++\n{0}\n+++++++++++++ /LOG ++++++++++++++++++".format(igloo_info["log"])
	else:
		print "\tFW version (top): {0}".format(igloo_info["version_fw_top"])
	if (igloo_info["version_fw_bot"] == "00.00"):
		print "\tERROR: There was a problem fetching the IGLOO's bottom FPGA information."
		print "\tThe log is below:\n++++++++++++++ LOG ++++++++++++++++++\n{0}\n+++++++++++++ /LOG ++++++++++++++++++".format(igloo_info["log"])
	else:
		print "\tFW version (bottom): {0}".format(igloo_info["version_fw_bot"])

def print_qie_info_1(ts, crate, slot, qie_card):
	qie_info = qie.get_info(ts, crate, slot, qie_card)
	igloo_info = qie_info["igloo"]
	bridge_info = qie_info["bridge"]
	print "* QIE card (crate {0}, slot {1:02d}, qie card {2}) =================".format(crate, slot, qie_card)
	if (igloo_info["version_fw"] == "00.00"):
		print "\tERROR: There was a problem fetching the IGLOO's top FPGA information."
#		print "\tThe log is below:\n++++++++++++++ LOG ++++++++++++++++++\n{0}\n+++++++++++++ /LOG ++++++++++++++++++".format(igloo_info["log"])
	else:
		print "\tIGLOO2 FW version: {0}".format(igloo_info["version_fw"])
	if (bridge_info["version_fw"] == "00.00.0000"):
		print "\tERROR: There was a problem fetching the BRIDGE information."
#		print "\tThe log is below:\n++++++++++++++ LOG ++++++++++++++++++\n{0}\n+++++++++++++ /LOG ++++++++++++++++++".format(bridge_info["log"])
	else:
		print "\tBRIDGE FW version: {0}".format(bridge_info["version_fw"])

def print_qie_info(ts):
	for crate, slots in ts.fe.iteritems():
		for slot in slots:
			for qie_card in range(1, ts.qie_cards_per_slot+1):
				print_qie_info_1(ts, crate, slot, qie_card)
# /FUNCTIONS

# MAIN:
if __name__ == "__main__":
	name = ""
	if len(sys.argv) == 1:
		name = "904"
	elif len(sys.argv) == 2:
		name = sys.argv[1]
	else:
		name = "904"
	ts = teststand(name)
	print "\n>> Finding the versions of the {0} teststand...".format(name)
	#print_amc13_info(ts)
	#print_glib_info(ts)
	#print_uhtr_info(ts)
	#print_ngccm_info(ts)
	print_qie_info(ts)
##	print_bridge_info(ts, 1, 2)
##	print_igloo_info(ts, 1, 1)
# /MAIN
