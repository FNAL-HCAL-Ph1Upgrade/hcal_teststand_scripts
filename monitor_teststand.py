####################################################################
# Type: SCRIPT                                                     #
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

N_ACTIVE_LINKS = 7

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
## Log parsing:
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
			log_parsed["links"]["links"] = ast.literal_eval(log_parsed["links"]["lines"][0].split("links:")[-1])
			log_parsed["links"]["orbits"] = ast.literal_eval(log_parsed["links"]["lines"][1].split("orbit:")[-1])
			log_parsed["links"]["adc"] = ast.literal_eval(log_parsed["links"]["lines"][2].split("meanADC:")[-1])

	return log_parsed

## Checks:
def check_temps(log_parsed):
	result = False
	error = ""
	try:
		temps = []
		if "ERROR" not in log_parsed["temperatures"]["registers"]["Crate 1 -> RM 1"]:
			temps.append(float(log_parsed["temperatures"]["registers"]["Crate 1 -> RM 1"]))
		else:
			temps.append(-1)
		if "ERROR" not in log_parsed["temperatures"]["registers"]["Crate 1 -> RM 2"]:
			temps.append(float(log_parsed["temperatures"]["registers"]["Crate 1 -> RM 2"]))
		else:
			temps.append(-1)

		if max(temps) < 65:
			result = True
		else:
			error += "ERROR: Crate 1 -> RM 1 -> {0}\n".format(log_parsed["registers"]["registers"]["Crate 1 -> RM 1"])
			error += "ERROR: Crate 1 -> RM 2 -> {0}\n".format(log_parsed["registers"]["registers"]["Crate 1 -> RM 2"])

	except Exception as ex:
		error += str(ex)
		print ex
	return check(result=result, error=error.strip(), scale=1)

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

def check_ngccm_static_regs(log_parsed):
	# This does not seem to be implemented for HE. 
	# ONES: 0x5050505
	# ZEROES: 0x7070707
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

def check_link_number(log_parsed):
	result = False
	error = ""
	try:
		links = log_parsed["links"]["links"]
		if len(links) == N_ACTIVE_LINKS:
			result = True
		else:
			error += "ERROR: There weren't {0} active links! The links are {1}.\n".format(N_ACTIVE_LINKS, links)
	except Exception as ex:
		error += str(ex)
		print ex
	return check(result=result, error=error.strip(), scale=0)

def check_link_orbits(log_parsed):
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
	except Exception as ex:
		error += str(ex)
		print ex
	return check(result=result, error=error.strip(), scale=0)

def check_link_adc(log_parsed):
	result = False
	error = ""
	try:
		adcs_per_link = [[float(link[i]) for i in range(len(link))] for link in log_parsed["links"]["adc"]]
		adcs = []
		for link in adcs_per_link:
			adcs.extend(link)
		# TODO: tune this threshold, will depend on whether we read out CM
		if (min(adcs) > 0 and max(adcs) < 50):
			result = True
		else:
			error += "ERROR: The pedestal values are wrong! Look: {0}.\n".format(adcs)
	except Exception as ex:
		error += str(ex)
		print ex
	return check(result=result, error=error.strip(), scale=0)

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

## Actions:
def send_email(subject="", body=""):
	msg = MIMEText(body)
	msg['Subject'] = subject
	msg['From'] = "alerts@teststand.hcal"
	msg['To'] = ""
	
	s = smtplib.SMTP('slmp-550-22.slc.westdc.net')
	s.login("alerts@connivance.net", "Megash4rk")
	s.sendmail(
		"alerts@connivance.net", 
		[
#			"tote@physics.rutgers.edu",
#			"sdg@cern.ch",
#			"tullio.grassi@gmail.com",
#			"yw5mj@virginia.edu",
#			"whitbeck.andrew@gmail.com",
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

def disable_qie(ts, crate=1):
	cmds = [
		"put HE{0}-bkp_pwr_enable 0".format(crate),
	]
	return ngccm.send_commands_parsed(ts.ngfec_port, cmds)["output"]

# /FUNCTIONS

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
