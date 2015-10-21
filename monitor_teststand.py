####################################################################
# Type: MODULE                                                     #
#                                                                  #
# Description: This reads teststand logs to find errors. There are #
# minor and major errors, both are recorded. In addition, major    #
# errors trigger an email to be sent to a few people.              #
####################################################################

from hcal_teststand import *
from hcal_teststand.hcal_teststand import teststand
from hcal_teststand.utilities import *
import sys
import os
from optparse import OptionParser
from time import sleep, time
import ast
import smtplib		# For emailing.
from email.mime.text import MIMEText		# For emailing.
import pexpect


# CLASSES:
class check:
	# Construction:
	def __init__(self, result=False, error="", scale=0):
		self.result = result
		self.error = error
		self.scale = scale
	
	# Boolean behavior:
	def __nonzero__(self):
		return self.result
	
	# String behavior:
	def __str__(self):
		return "<check object: result = {0}, scale = {1}, error = \"{2}\">".format(self.result, self.scale, self.error)
# /CLASSES

# FUNCTIONS:

## ------------------
## -- Log parsing: --
## ------------------

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
	
	# Format "links" values:
	if "links" in log_parsed.keys():
		if log_parsed["links"]:
			# Turn the list of links into a python list.
			# find the line with "links:"
			linkindex = -1
			for il, l in enumerate(log_parsed["links"]["lines"]):
				if "links:" in l:
					linkindex = il
					break
			if linkindex != -1:		
				log_parsed["links"]["links"] = ast.literal_eval(log_parsed["links"]["lines"][linkindex].split("links:")[-1])
				log_parsed["links"]["orbits"] = ast.literal_eval(log_parsed["links"]["lines"][linkindex+1].split("orbit:")[-1])
				log_parsed["links"]["adc"] = ast.literal_eval(log_parsed["links"]["lines"][linkindex+2].split("meanADC:")[-1])
			else:
				print "No link information from the spy!"
	return log_parsed


## -------------------------
## -- Check temperatures: --
## -------------------------

def check_temps(ts, ts_status, log_parsed):
	result = False
	error = ""
	try:
		temps = []
		for ix, i in enumerate(ts.fe_crates):
			for j in ts.qie_slots[ix]:
                                temp = log_parsed["temperatures"]["registers"]["Crate {0} -> RM {1}".format(i,j)]
				if "ERROR" in temp or temp.strip() == "":
					temps.append(-1)
				else:
                                        try:
                                                temp_f = float(temp)
                                                temps.append(temp_f)
						tempdiff = abs(temp_f - ts_status.controlcards[i,j].peltier_targettemperature_f)
                                                # Also check what the target temperature was:
                                                if tempdiff > 1.5*ts_status.controlcards[i,j].peltier_adjustment_f:
                                                        error += "ERROR: Temperature deviation in crate {0}, slot {1}: target was {2}, measured was {3}".format(i,j,ts_status.controlcards[i,j].peltier_targettemperature_f, temp)
                                                        #send_email("Temperature deviation!","Measured temperature was {0}".format(temp_f))
							if tempdiff > 3:
								send_email("HE teststand ({0}): Temperature deviation".format(ts.name),
									   "Measured temperature was {0}".format(temp_f))
                                                else:
                                                        result = True
                                        except ValueError:
                                                error += "No valid temperature for crate {0}, slot {1}: {2}\n".format(i,j,temp)
                                                temps.append(-1)
                                        
	except Exception as ex:
		error += str(ex)
		print ex
	return check(result=result, error=error.strip(), scale=1)

## ----------------------
## -- Check LHC clock: --
## ----------------------

def check_clocks(log_parsed):
	result = False
	error = ""
	try:
		lhc_clock = -1
		if "ERROR" not in log_parsed["registers"]["registers"]["get fec1-LHC_clk_freq"]:
			lhc_clock = int(log_parsed["registers"]["registers"]["get fec1-LHC_clk_freq"], 16)
		if lhc_clock > 400776 and lhc_clock < 400790: # changed from 400788 since fnal clock is at 400788
			result = True
		else:
			error += "ERROR: get fec1-LHC_clk_freq -> {0} ({1})\n".format(log_parsed["registers"]["registers"]["get fec1-LHC_clk_freq"], lhc_clock)
	except Exception as ex:
		error += str(ex)
		print ex
	return check(result=result, error=error.strip(), scale=1)

## ---------------------------
## -- Obsolete check for HE --
## ---------------------------

def check_ngccm_static_regs(log_parsed):
	# Do this stuff for the igloo and bridge
	result_zeroes = False
	result_ones = False
	error = ""
	try:
		if log_parsed["registers"]["registers"]["get HE1-mezz_ONES"] == "'0xffffffff 0xffffffff 0xffffffff 0xffffffff'":
			result_ones = True
		else:
			error += "ERROR: get HE1-mezz_ONES -> {0}\n".format(log_parsed["registers"]["registers"]["get HE1-mezz_ONES"])
	except Exception as ex:
		print ex
	try:
		if log_parsed["registers"]["registers"]["get HE1-mezz_ZEROES"] == "'0 0 0 0'":
			result_zeroes = True
		else:
			error += "ERROR: get HE1-mezz_ZEROES -> {0}\n".format(log_parsed["registers"]["registers"]["get HE1-mezz_ZEROES"])
	except Exception as ex:
		error += str(ex)
		print ex
	result = False
	if result_zeroes and result_ones:
		result = True
	return check(result=result, error=error.strip(), scale=0)

## -------------------------------
## -- Check status of the links --
## -------------------------------

def check_link_number(ts_status,log_parsed):
	result = False
	error = ""
	try:
		links = log_parsed["links"]["links"]
		if len(links) == ts_status.links.n_active_links:
			result = True
		else:
			error += "ERROR: There weren't {0} active links! The links are {1}.\n".format(ts_status.links.n_active_links, links)
	except Exception as ex:
		error += str(ex)
		print ex
	return check(result=result, error=error.strip(), scale=0)

def check_link_orbits(log_parsed):
        # This should also be already checked in the other linkstatus function
	result = False
	error = ""
	try:
		orbits = log_parsed["links"]["orbits"]
		orbits = [float(orbit) for orbit in orbits]
		results = [True if orbit < 11.3 and orbit > 11.1 else False for orbit in orbits ]
		if False not in results:
			result = True
		else:
			error += "ERROR: The link orbit rates are wrong! Look: {0}.\n".format(orbits)
        except ValueError as vex:
                error += "Probably could not convert the orbit rate to float.\n" + str(vex)
                print vex
	except Exception as ex:
		error += str(ex)
		print ex
	return check(result=result, error=error.strip(), scale=0)

def check_link_adc(ts_status, log_parsed):
	result = False
	error = ""
	try:
		adcs_per_link = [[float(link[i]) for i in range(len(link))] for link in log_parsed["links"]["adc"]]
		adcs = []
		for link in adcs_per_link:
			adcs.extend(link)
		if (min(adcs) > 0 and max(adcs) < ts_status.links.maxADC
		    and sum(adcs)/len(adcs) < ts_status.links.maxAveADC):
			result = True
		else:
			error += "ERROR: The pedestal values are wrong! Look: {0}.\n".format(adcs)
	except ValueError as vex:
		error += "Probably could not convert the adc counts to float.\n" + str(vex)
		print vex
	except Exception as ex:
		error += str(ex)
		print ex
	return check(result=result, error=error.strip(), scale=0)

def check_link_status(statData):
        problemLinks = []

        linksGood = True
        # Problem type: 
        # type 1 needs a link init
        # type 2 is orbit rate related, which means just wait to see if it improves
        problemType = 0  
        for link in statData:
                if statData[link]['On']:
                        if statData[link]['badAlign']>100:
				# Put it rather high, seems like there are some link issues
                                linksGood = False
                                if not link in problemLinks: problemLinks.append(link)
                                problemType = 1
                        if not statData[link]['orbitRates'] == "1.12e+01":
                                linksGood = False
                                if not link in problemLinks: problemLinks.append(link)
                                if problemType==0: problemType=2
                        if statData[link]['badData']>0:
                                linksGood = False
                                if not link in problemLinks: problemLinks.append(link)
                                problemType = 1
                        if statData[link]['badDataRate']>0:
                                linksGood = False
                                if not link in problemLinks: problemLinks.append(link)
                                problemType = 1
                        if statData[link]['alignDelta']==0 or statData[link]['alignDelta'] > 14:
                                linksGood = False
                                if not link in problemLinks: problemLinks.append(link)
                                problemType = 1
                        if statData[link]['alignDelta'] != statData[link]['alignOcc']:
                                linksGood = False
                                if not link in problemLinks: problemLinks.append(link)
                                problemType = 1

        return linksGood, problemLinks, problemType


## ------------------------------
## -- Check various registers: --
## ------------------------------

def check_qie_registers(qie_status, log_parsed):
        result = True
        error = []
	scale = 0
        for crate_slot_qie, qie_register in qie_status.iteritems():
                crate, slot, qienum = crate_slot_qie
                # do the checks on all qie registers
                regs = [reg for reg in dir(qie_register) if not reg.startswith("__")]
                for reg in regs:
                        # Find it in the logs, and check whether it matches
			try:
				log_reg = log_parsed["registers"]["registers"]["get HE{0}-{1}-QIE{2}_{3}".format(crate, slot, qienum, reg)]
				if "ERROR" in log_reg or "NACK" in log_reg:
					result = False
					scale = 1
					error.append("QIE register ( HE{0}-{1}-QIE{2}_{3}) contained error: {4} ".format(crate, slot, qienum, reg, log_reg))
					continue
				log_reg_i = int(log_reg,0)
				exp_reg = getattr(qie_register, reg)
				if exp_reg != log_reg_i:
					# Probably a SEU
					error.append("QIE SEU candidate: get HE{0}-{1}-QIE{2}_{3} returned {4}, we expected {5}.".format(crate, slot, qienum, reg, log_reg, exp_reg))
					result = False
			except KeyError:
				result = False
				scale = 1
				error.append("QIE register HE{0}-{1}-QIE{2}_{3} could not be found in the log.".format(crate, slot, qienum, reg))
			except ValueError:
				result = False
				scale = 1
				error.append("Could not convert {0} to integer (QIE HE{1}-{2}-QIE{3}_{4})".format(log_reg, crate, slot, qienum, reg))

        return check(result=result, error="\n".join(error), scale=scale)

def check_controlcard_registers(controlcard_status, log_parsed):
        result = True
        error = []
	scale = 0
        for crate_slot, cc_register in controlcard_status.iteritems():
                crate, slot = crate_slot
                regs = [reg for reg in dir(cc_register) if not reg.startswith("__")]
                for reg in regs:
                        # Find it in the logs, and check whether it matches
			try:
                            log_reg = log_parsed["registers"]["registers"]["get HE{0}-{1}-{2}".format(crate, slot, reg)]
			    if "NACK" in log_reg and "biasmon" in reg:
				    error.append("Control Card SEU candidate: get HE{0}-{1}-{2} returned {3}".format(crate, slot, reg, log_reg))
				    result = False
				    continue

                            exp_reg = getattr(cc_register, reg)
                            if reg.endswith("_f"):
                                    # we are dealing with a float, so should not require exact match
                                    # For now this is just the biasmon
                                    if abs(exp_reg - float(log_reg)) > 1.:
                                            error.append("Control Card error: get HE{0}-{1}-{2} returned {3}, we expected {4}.".format(crate, slot, reg, log_reg, exp_reg))
                                            result = False
                            else:
                                    if exp_reg != int(log_reg,0):
                                            # Probably a SEU, these are the peltier registers
                                            error.append("Control Card error: get HE{0}-{1}-{2} returned {3}, we expected {4}.".format(crate, slot, reg, log_reg, exp_reg))
                                            result = False
                                            
			except KeyError:
				result = False
				scale = 1
				error.append("Control card register HE{0}-{1}-{2} could not be found in the log.".format(crate, slot, reg))
			except ValueError:
				result = False
				scale = 1
				error.append("Could not convert {0} to integer or float (Control card HE{1}-{2}-{3})".format(log_reg, crate, slot, reg))

        return check(result=result, error="\n".join(error), scale=scale)

def check_bridge_registers(bridge_status, log_parsed):
        result = True
        error = []
	scale = 0
        for crate_slot_card, bridge_register in bridge_status.iteritems():
                crate, slot, qiecard = crate_slot_card
		# do the checks on all bridge registers
                regs = [reg for reg in dir(bridge_register) if (not reg.startswith("__") and not "update" in reg )] 
                for reg in regs:
			try:
				log_reg = log_parsed["registers"]["registers"]["get HE{0}-{1}-{2}-B_{3}".format(crate, slot, qiecard, reg)]
				if "ERROR" in log_reg or "NACK" in log_reg:
					result = False
					scale = 1
					error.append("Bridge register ( HE{0}-{1}-{2}-B_{3}) contained error: {4} ".format(crate, slot, qiecard, reg, log_reg))
					continue
				log_reg_i = int(log_reg,0)
				if "COUNTER" in reg:
					# Check that it changed, and update the value
					prev_reg = getattr(bridge_register, reg)
					if log_reg_i != prev_reg:
						# all is OK
						getattr(bridge_register, "update_{0}".format(reg))(log_reg_i)
					else:
						result = False
						error.append("Bridge error: Counter did not go up: get HE{0}-{1}-{2}-B_{3} returned {4} again.".format(crate, slot, qiecard, reg, log_reg))
				else:
					exp_reg = getattr(bridge_register, reg)
					if log_reg_i != exp_reg:
						result = False
						# probably SEU, so no need for an email ;-)
						error.append("Bridge SEU candidate: get HE{0}-{1}-{2}-B_{3} returned {4}, we expected {5}".format(crate, slot, qiecard, reg, log_reg, exp_reg))
			except KeyError:
				result = False
				scale = 1
				error.append("Bridge register HE{0}-{1}-{2}-B_{3} could not be found in the log.".format(crate, slot, qiecard, reg))
			except ValueError:
				result = False
				scale = 1
				error.append("Could not convert {0} to integer (Bridge HE{1}-{2}-{3}-B_{4})".format(log_reg, crate, slot, qiecard, reg))
				
        return check(result=result, error="\n".join(error), scale=scale)


def check_igloo_registers(igloo_status, log_parsed, scale):
        result = True
        error = []
	scale = 0
        for crate_slot_card, igloo_register in igloo_status.iteritems():
                crate, slot, qiecard = crate_slot_card
                # do the checks on all igloo registers
                regs = [reg for reg in dir(igloo_register) if (not reg.startswith("__") and not "update" in reg )] 
                for reg in regs:
			# Skip some registers for the sparse log
			if scale == 0 and "CntrReg" in reg:
				continue
			if scale == 0 and "_ck_ph" in reg and not "Qie41_ck_ph" in reg:
				continue
			try:
				log_reg = ""
				if "_ck_ph" in reg:
					log_reg = log_parsed["registers"]["registers"]["get HE{0}-{1}-{2}".format(crate, slot, reg)]
				else:
					log_reg = log_parsed["registers"]["registers"]["get HE{0}-{1}-{2}-i_{3}".format(crate, slot, qiecard, reg)]
				if "ERROR" in log_reg or "NACK" in log_reg:
					result = False
					scale = 1
					error.append("Igloo register ( HE{0}-{1}-{2}-i_{3}) contained error: {4} ".format(crate, slot, qiecard, reg, log_reg))
					continue
    
				log_reg_i = int(log_reg,0)
				if "CapIdErrLink1" in reg or "CapIdErrLink2" in reg:
					# just update it for now
					getattr(igloo_register, "update_{0}".format(reg))(log_reg_i)
				elif "count" in reg and not "CapIdErrLink3" in reg:
					# Check that it changed, and update the value
					prev_reg = getattr(igloo_register, reg)
					if log_reg_i != prev_reg:
						getattr(igloo_register, "update_{0}".format(reg))(log_reg_i)
					else:
						result = False
						error.append("Igloo error: Counter did not go up: get HE{0}-{1}-{2}-i_{3} returned {4} again.".format(crate, slot, qiecard, reg, log_reg))
				else:
					exp_reg = getattr(igloo_register, reg)
					if log_reg_i != exp_reg:
						result = False
						# probably SEU
						error.append("Igloo SEU candidate: get HE{0}-{1}-{2}-i_{3} returned {4}, we expected {5}".format(crate, slot, qiecard, reg, log_reg, exp_reg))
			except KeyError:
				result = False
				scale = 1
				error.append("Igloo register HE{0}-{1}-{2}-i_{3} could not be found in the log.".format(crate, slot, qiecard, reg))
			except ValueError:
				result = False
				scale = 1
				error.append("Could not convert {0} to integer (Igloo HE{1}-{2}-{3}-i_{4})".format(log_reg, crate, slot, qiecard, reg))
				
        return check(result=result, error="\n".join(error), scale=scale)


def check_registers(ts_status, log_parsed, scale):
        # Check the qies        
        check_qies = check_qie_registers(ts_status.qies, log_parsed)
        check_controlcards = check_controlcard_registers(ts_status.controlcards, log_parsed)
	check_bridges = check_bridge_registers(ts_status.bridges, log_parsed)
	check_igloos = check_igloo_registers(ts_status.igloos, log_parsed, scale)
        return [check_qies, check_controlcards, check_bridges, check_igloos]

## ------------------
## -- Check power: --
## ------------------

def check_power(log_parsed):
	# Cannot test at FNAL
	result = False
	error = ""
	try:
		V = float(log_parsed["power"]["lines"][0].split()[0])
		I = float(log_parsed["power"]["lines"][1].split()[0])
		if (I > 1.13 and I < 3.9) or ( V == -1):
#		if (I > 3.0 and I < 3.6) or ( V == -1):
			result = True
		else:
			error += "ERROR: The current to the FE crate is not good! I = {0}, V = {1}\n".format(I, V)
	except Exception as ex:
		error += str(ex)
		print ex
	return check(result=result, error=error.strip(), scale=2)


## -------------------------
## -- Check control link: --
## -------------------------

def check_cntrl_link(log_parsed):
	result = False
	error = ""
	status = -1
	try:
		if "ERROR" not in log_parsed["registers"]["registers"]["get fec1-sfp1_status.RxLOS"]:
			status = int(log_parsed["registers"]["registers"]["get fec1-sfp1_status.RxLOS"])
		if status == 0:
			result = True
		else:
			error += "ERROR: get fec1-sfp1_status.RxLOS -> {0}\n".format(log_parsed["registers"]["registers"]["get fec1-sfp1_status.RxLOS"], status)
	except Exception as ex:
		error += str(ex)
		print ex
	return check(result=result, error=error.strip(), scale=1)


## ----------------------
## -- Various actions: --
## ----------------------

def send_email(subject="", body=""):
	msg = MIMEText(body)
	msg['Subject'] = subject
	msg['From'] = "alerts@teststand.hcal"
	msg['To'] = ""
	
	s = smtplib.SMTP_SSL('slmp-550-22.slc.westdc.net',465)
	s.login("alerts@connivance.net", "Megash4rk")
	s.sendmail(
		"alerts@connivance.net", 
		[
#			"tote@physics.rutgers.edu",
#			"sdg@cern.ch",
#			"tullio.grassi@gmail.com",
#			"yw5mj@virginia.edu",
#			"whitbeck.andrew@gmail.com",
                        "pastika@fnal.gov",
			"nadja.strobbe@gmail.com"
		],
		msg.as_string()
	)
	s.quit()

def setup_157():
	p = pexpect.spawn('python ts_setup.py -v 1')		# Run script.
	p.expect(pexpect.EOF)		# Wait for the script to finish.
	raw_output = p.before.strip()		# Collect all of the script's output.
	return raw_output

def power_cycle(n=10):
	log = ""
	print "> Conducting a power cycle ..."
	log += "Conducting a power cycle ...\n"
	print "> Disabling power supply ..."
	log += "Disabling power supply ...\n"
	log += ts_157.enable_power(enable=0)
	log += "\n"
	print "> Sleeping {0} seconds ...".format(n)
	log += "Sleeping {0} seconds ...\n".format(n)
	sleep(n)
	print "> Configuring power supply ..."
	log += "Configuring power supply ...\n"
	config_result = ts_157.config_power()
	log += config_result
	log += "\n"
	if ("OVP 11.00" in config_result) and ("V 10.00" in config_result) and ("I 4.40" in config_result):
		print "> Enabling power supply ..."
		log += "Enabling power supply ...\n"
		log += ts_157.enable_power(enable=1)
		log += "\n"
		print "> Setting up teststand ..."
		log += "Setting up teststand ...\n"
		raw_output = setup_157()
		log += raw_output + "\n"
	else:
		print "> [!!] Power cycle aborted. The OVP wasn't 11 V."
		log += "[!!] Power cycle aborted. The OVP wasn't 11 V.\n"
	return log

# This is probably not useful for the radiation test
def disable_qie(ts, crate=1):
	cmds = [
		"put HE{0}-bkp_pwr_enable 0".format(crate),
                ]
	return ngccm.send_commands_parsed(ts.ngfec_port, cmds)["output"]

# /FUNCTIONS

def printNiceLinkInfo(info):
	statData[link]['alignBCN']
	nice = []
	for link, link_info in info.iteritems():
		nice.append("Link {0}\n------------\n".format(link))
		for counter, value in link_info.iteritems():
			nice.append("    {0}:{1}\n".format(counter, value))

	return "".join(nice)

## ---------------------------
## -- Main monitor function --
## ---------------------------

def monitor_teststand(ts, ts_status, logpath, link_status, scale):
        """
        Monitor the current state of the teststand, and send alerts if something is wrong.
        
        Arguments:
        ts -- a teststand object
        ts_status -- a TestStandStatus object
        logpath -- the path to the log file
        link_status -- the dictionary with link information
        """

	# Make sure the log file actually exists
	if not os.path.isfile(logpath):
		print "Log file does not exist!"
		print "Is there a problem with the logger?"
		email_body = """Hi there,
There seems to be a problem with the logger. 
The monitor cannot find the log that should have been created just now.
Please check the system asap!

Thanks!!
"""
		send_email(subject="!!Problem with HE log_teststand.py ({0})!!".format(ts.name), body=email_body)
		return
	else:
		print "> Monitoring log {0} ...".format(logpath)

        # First check the health of the links
        for (uhtr_, statData) in link_status:
                linksGood, problemLinks, problemType = check_link_status(statData)
                if not linksGood:
                        print "Problem in uHTR in crate {0}, slot {1}, with Links: {2}".format(uhtr_.crate, uhtr_.slot, problemLinks)
                        if problemType == 1:
                                print "Initializing links"
                                uhtr.initLinks_per_uhtr(ts, uhtr_.crate, uhtr_.slot, uhtr_.ip,
                                                        ts_status.links.OrbitDelay,
                                                        ts_status.links.Auto_Realign,
                                                        ts_status.links.OnTheFlyAlignment,
                                                        ts_status.links.CDRreset,
                                                        ts_status.links.GTXreset)
                                print "Checking link status again, and sending email"
                                sleep(2)
                                raw_status = uhtr.parseLinkStatus(uhtr.linkStatus_per_uhtr(ts=ts,
                                                                                           crate=uhtr_.crate,
                                                                                           slot=uhtr_.slot,
                                                                                           ip=uhtr_.ip,
                                                                                           control_hub=ts.control_hub)[uhtr_.crate,uhtr_.slot])
				link_error_info = printNiceLinkInfo(statData)
                                send_email(subject="HE teststand ({0}): links reinitialized!".format(ts.name), body="Link status was: \n{0}\n\nLink status after reinitialization is\n{1}".format(link_error_info, raw_status[1]))
                                # TODO: add while loop to initialize extra times if necessary
                        elif problemType == 2:
                                print "I'm waiting to see if the problem persists. Nothing catastrophic going on for now"

	print "Finished checking links"

	# Now open the log and parse it
	with open(logpath) as f_in:
		parsed = parse_log(f_in.read())
				
		# Perform checks:
		error_log = ""
		checks = []
		checks.append(check_temps(ts, ts_status, parsed))
		#checks.append(check_clocks(parsed))
		#cntrl_link = check_ngccm_static_regs(parsed)
		#checks.append(cntrl_link)
		checks.append(check_link_number(ts_status, parsed))
		checks.append(check_link_orbits(parsed))
		checks.append(check_link_adc(ts_status, parsed))
		#checks.append(check_power(parsed))
		#checks.append(check_cntrl_link(parsed))
                checks.extend(check_registers(ts_status, parsed, scale))

		#checks.append(check(result=False, scale=1, error="This is a fake error message"))
					
		# Control link status:
		#if status_last != -1:
		#	if cntrl_link.result != status_last:
		#		pass
		#		send_email(subject="Update: control link", body="The state of the control link changed from {0} to {1}.".format(status_last, cntrl_link.result))
		#status_last = cntrl_link.result
					
		# Deal with failed checks:
		failed = [c for c in checks if not c.result]
		if failed:			
			print "Found {0} failed checks. Dealing with them now.".format(len(failed))
			# Set up error log:
			error_log = ""
			for c in failed:
				print c.result, c.error
				error_log += "{0} (scale {1})\n".format(c.error, c.scale)
					
			# Deal with critical errors:
			critical = [c for c in failed if c.scale > 0]
			if critical:
				print "> CRITICAL ERROR DETECTED!"
							
				# Prepare email:
				email_subject = "ERROR at HE teststand ({0})".format(ts.name)
				email_body = "Critical errors were detected while reading \"{0}\".\nThe errors are listed below:\n\n".format(logpath)
				for c in critical:
					email_body += c.error + " (scale {0})".format(c.scale)
					email_body += "\n"
				email_body += "\n"
				
				# Try to fix the major problems immediately
				# Power cycle if any have scale 2 or greater:
				#if [c for c in critical if c.scale > 1]:
					#power_log = power_cycle()
					#power_log = setup_157()
					#power_log = str(disable_qie(ts))
					#email_body += "A power cycle was triggered. Here's how it went:\n\n"
					#email_body += "A power enable cycle was triggered. Here's how it went:\n\n"
					#email_body += "A QIE card disable was triggered. Here's how it went:\n\n"
					#email_body += power_log
					#email_body += "\n"
					#error_log += "A power cycle was triggered. Here's how it went:\n\n"
					#error_log += "A power enable cycle was triggered. Here's how it went:\n\n"
					#error_log += "A QIE card disable was triggered. Here's how it went:\n\n"
					#error_log += power_log
							
				# Send email:
				email_body += "\nHave a nice day!"
				try:
					print "> Sending email ..."
					send_email(subject=email_subject, body=email_body)
					print "> Email sent."
				except Exception as ex:
					print "ERROR!!!"
					print ex
					error_log += str(ex)
					error_log += "\n"
							
				if [c for c in critical if c.scale > 1]:
					print "> Waiting 2 minutes after the power cycle before going back to monitoring logs ..."
					sleep(2*60)
							
			# Write error log:
			logpathinfo = logpath.rpartition("/")
			if not os.path.exists("{0}/error_logs".format(logpathinfo[0])):
				os.makedirs("{0}/error_logs".format(logpathinfo[0]))
			with open("{0}/error_logs/errors_{1}".format(logpathinfo[0], logpathinfo[2]), "w") as out:
				out.write(error_log)
			print "Wrote error log"
		else:
			print "All checks passed"
					


# MAIN:
if __name__ == "__main__":
	# Script arguments:
	parser = OptionParser()
	parser.add_option("-t", "--teststand", dest="ts",
		default="157",
		help="The name of the teststand you want to use (default is %default). Unless you specify the path, the directory will be put in \"data\".",
		metavar="STR"
	)
	parser.add_option("-d", "--directory", dest="d",
		default="data/ts_157",
		help="The directory containing the log files (default is %default).",
		metavar="STR"
	)
	parser.add_option("--date", dest="date",
			  default="today",
			  help = "The date for which you want to parse the logs (default:%default)",
			  metavar = "YYMMDD")
	(options, args) = parser.parse_args()
	name = options.ts
	directory = options.d
	date = options.date
	
	# Set up teststand:
	ts = teststand(name)
	
	# Print information:
	if os.path.exists(directory):
		print "> Monitoring the {0} directory.".format(directory)
	else:
		print "> The {0} directory doesn't exist.".format(directory)
	
	# Logging loop:
	z = True
	n = 0
	n_sleep = 0
	last_log = ""
	t_last_log = time()
	status_last = -1
	while z == True:
		# Set up variables:
		dt_last_log = time() - t_last_log
	
		# Find subdirectory named after the date and construct the full path:
		if options.date == "today":
			date = time_string()[:6]
		path = directory + "/" + date
		
		if os.path.exists(path):
			# Get a list of logs from the path:
			logs = []
			for item in os.listdir(path):
				if os.path.isfile(os.path.join(path, item)):
					logs.append(item)
			logs = sorted(logs)		# Sorted alphabetically, which is chronological in this case.
#			print logs
			
			# Construct the queue, the files to check:
			if not last_log:
				last_log = logs[-2]
			next_log = logs[-1] # should be the last element of the list, so the newest log
#			queue = logs[logs.index(last_log) + 1:]		# The queue is all the log files after the last one checked. (Yes, this will skip the first one if no "last" is specified. Whatever.
			queue = [next_log]

			if next_log != last_log:
				print last_log
				print next_log
				# Open and check logs in queue:
				for log in queue:
					print "> Monitoring log {0} ...".format(log)
					with open("{0}/{1}".format(path, log)) as f_in:
						parsed = parse_log(f_in.read())
#					print parsed
				
					# Perform checks:
					error_log = ""
					checks = []
					checks.append(check_temps(parsed))
					checks.append(check_clocks(parsed))
					#cntrl_link = check_ngccm_static_regs(parsed)
					#checks.append(cntrl_link)
					checks.append(check_link_number(parsed))
					checks.append(check_link_orbits(parsed))
					#checks.append(check_power(parsed))
					checks.append(check_cntrl_link(parsed))
					checks.append(check_link_adc(parsed))
#					checks.append(check(result=False, scale=1, error="This is a fake error message"))
					
					# Control link status:
					#if status_last != -1:
					#	if cntrl_link.result != status_last:
					#		pass
					#		send_email(subject="Update: control link", body="The state of the control link changed from {0} to {1}.".format(status_last, cntrl_link.result))
					#status_last = cntrl_link.result
					
					# Deal with failed checks:
					failed = [c for c in checks if not c.result]
					if failed:
						
						# Set up error log:
						error_log = ""
						for c in failed:
							print c.error
							error_log += "{0} (scale {1})".format(c.error, c.scale)
							error_log += "\n"
						
						# Deal with critical errors:
						critical = [c for c in failed if c.scale > 0]
						if critical:
							print "> CRITICAL ERROR DETECTED!"
							
							# Prepare email:
							email_subject = "ERROR at HE teststand"
							email_body = "Critical errors were detected while reading \"{0}\".\nThe errors are listed below:\n\n".format(log)
							for c in critical:
								email_body += c.error + " (scale {0})".format(c.scale)
								email_body += "\n"
							email_body += "\n"
							
							# Power cycle if any have scale 2 or greater:
							if [c for c in critical if c.scale > 1]:
#								power_log = power_cycle()
#								power_log = setup_157()
								power_log = str(disable_qie(ts))
#								email_body += "A power cycle was triggered. Here's how it went:\n\n"
#								email_body += "A power enable cycle was triggered. Here's how it went:\n\n"
								email_body += "A QIE card disable was triggered. Here's how it went:\n\n"
								email_body += power_log
								email_body += "\n"
#								error_log += "A power cycle was triggered. Here's how it went:\n\n"
#								error_log += "A power enable cycle was triggered. Here's how it went:\n\n"
								error_log += "A QIE card disable was triggered. Here's how it went:\n\n"
								error_log += power_log
							
							# Send email:
							email_body += "\nHave a nice day!"
							try:
								print "> Sending email ..."
								#send_email(subject=email_subject, body=email_body)
								print "> Email sent."
							except Exception as ex:
								print "ERROR!!!"
								print ex
								error_log += str(ex)
								error_log += "\n"
							
							if [c for c in critical if c.scale > 1]:
								print "> Waiting 2 minutes after the power cycle before going back to monitoring logs ..."
								sleep(2*60)
							
						# Write error log:
						if not os.path.exists("{0}/error_logs".format(path)):
							os.makedirs("{0}/error_logs".format(path))
						with open("{0}/error_logs/errors_{1}".format(path, log), "w") as out:
							out.write(error_log)
					
					# Conclude:
					last_log = log
					t_last_log = time()
					n_sleep = 0
				
#					z = False
#					break
			else:
				if dt_last_log > 60*60:
					email_body = "ERROR: I think the logging code crashed."
					print "> {0}".format(email_body)
					#send_email(subject="ERROR at teststand 157", body=email_body)
					z = False
				sleep(1)
				n_sleep += 1
				if n_sleep == 1:
					print "> Waiting for the next log ..."
		else:
			print "> There are no log files for today. ({0})".format(n)
			n += 1
			sleep(60)
		if n > 3:
			z = False
# /MAIN
