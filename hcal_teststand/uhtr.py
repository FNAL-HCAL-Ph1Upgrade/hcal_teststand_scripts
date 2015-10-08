####################################################################
# Type: MODULE                                                     #
#                                                                  #
# Description: This module contains functions for talking to the   #
# uHTRs.                                                           #
####################################################################
#
from re import search
from subprocess import Popen, PIPE
import hcal_teststand
import qie
import meta
import ngfec
from ROOT import *
from time import sleep
import os

# VARIABLES:
cmds_default = ["0", "exit", "-1"]
# /VARIABLES

# CLASSES:
class uhtr:
	# Construction:
	def __init__(self, ts=None, crate=None, slot=None, ip=None):
		self.ts = ts
		self.end = "be"
		self.be_crate = self.crate = crate
		self.be_slot = self.slot = slot
		self.ip = ip
		self.control_hub = ts.control_hub
		if ts:
			if "{0}_qie_map.json".format(ts.name) in os.listdir("configuration/maps"):
				links = get_links_from_map(ts=ts, crate=crate, slot=slot, end=self.end)
				if links:
					self.links = links
				else:
					self.links = []
			else:
				self.links = []
		else:
			self.links = []
	
	# String behavior
	def __str__(self):
		try:
			return "<uHTR in BE Crate {0}, BE Slot {1}: IP = {2}>".format(self.crate, self.slot, self.ip)
		except Exception as ex:
#			print ex
			return "<empty uhtr object>"
	
	# Methods:
	def update(self):
		try:
			info = get_info(ip=self.ip, control_hub=self.control_hub)[self.ip]
#			print info
			self.fw_type_front = info["fw_type_front"]
			self.fw_front = info["fw_front"]
			self.fw_type_back = info["fw_type_back"]
			self.fw_back = info["fw_back"]
			self.fws = ["fws"]
			return True
		except Exception as ex:
			print ex
			return False
	
	def Print(self):
		print self
	
	def send_commands(self, cmds=cmds_default, script=False):
		return send_commands(control_hub=self.control_hub, ip=self.ip, cmds=cmds, script=script)
	
	def setup(self):
		return setup(ip=self.ip, control_hub=self.control_hub)
	# /Methods

class status:
	# Construction:
	def __init__(self, ts=None, status=[], crate=None, slot=None, ip={}, fws=[], links=[], dump=""):
		if not ts:
			ts = None
		self.ts = ts
		if not status:
			status = []
		self.status = status
		self.crate = crate
		self.slot = slot
		if not ip:
			ip = {}
		self.ip = ip
		if not fws:
			fws = []
		self.fws = fws
		if not links:
			links = []
		self.links = links
		self.dump = dump
	
	# String behavior
	def __str__(self):
		if self.ts:
			return "<uhtr.status object: {0}>".format(self.status)
		else:
			return "<empty uhtr.status object>"
	
	# Methods:
	def update(self):
		self.good = (False, True)[bool(self.status) and len(self.status) == sum(self.status)]
	
	def Print(self, verbose=True):
		if verbose:
			print "[{0}] uHTR in BE Crate {1}, BE Slot {2} status: {3} <- {4}".format(("!!", "OK")[self.good], self.crate, self.slot, ("BAD", "GOOD")[self.good], self.status)
			print "\tFWs: {0}".format(self.fws)
			print "\tLinks: {0}".format(self.links)
			print "\tIP: {0}".format(self.ip)
		else:
			print "[{0}] uHTR in BE Crate {1}, BE Slot {2} status: {3}".format(("!!", "OK")[self.good], self.crate, self.slot, ("BAD", "GOOD")[self.good])
	
	def log(self):
		output = "%% uHTR {0}, {1}\n".format(self.crate, self.slot)
		output += "{0}\n".format(int(self.good))
		output += "{0}\n".format(self.status)
		output += "{0}\n".format(self.fws)
		output += "{0}\n".format(self.links)
		output += "{0}\n".format(self.ip)
		output += "{0}\n".format(self.dump)
		return output.strip()
	# /Methods

class link:		# An object that represents a uHTR link. It contains information about what it's connected to.
	qie_half_labels = ['bottom', 'top']
	
	# CONSTRUCTION
	def __init__(self, ts="unknown", be_crate=-1, be_slot=-1, fe_crate=-1, fe_slot=-1, link_number=-1, qie_unique_id="unknown", qie_half=-1, qie_fiber=-1, on=False, qies=[-1, -1, -1, -1]):
		self.ts = ts
		self.be_crate = be_crate
		self.be_slot = be_slot
		self.fe_crate = fe_crate
		self.fe_slot = fe_slot
		self.n = link_number
		self.qie_unique_id = self.id = qie_unique_id
		self.qie_half = self.half = qie_half
		self.qie_half_label = self.half_label = "unknown"
		self.qie_fiber = qie_fiber
		self.on = on
		self.qies = qies		# The QIE numbers corresponding to the channel numbers of the link.
		if self.qie_half in [0, 1]: 
			self.qie_half_label = self.half_label = self.qie_half_labels[self.qie_half]
		try:
			self.uhtr_ip = self.ip = ts.uhtr_ip(crate, slot)
		except Exception as ex:
			self.uhtr_ip = self.ip = ""
	# /CONSTRUCTION
	
	# METHODS
	def get_data_spy(self, n_bx=50):
		data = get_data_spy(ts=self.ts, crate=self.be_crate, slot=self.be_slot, n_bx=n_bx, i_link=self.n)[(self.be_crate, self.be_slot)][self.n]
		if data:
			return data
		else:
			return False
	
	def Print(self):
		print "uHTR Info: BE Crate {0}, BE Slot {1}, Link {2}".format(self.be_crate, self.be_slot, self.n)
		print "QIE card ID:", self.qie_unique_id
		print "QIE card half:", self.qie_half_label
		print "Fiber:", self.qie_fiber
		print "Active:", (self.on == 1)
	# /METHODS
	
	def __str__(self):		# This just defines what the object looks like when it's printed.
		if self.n != -1:
			return "<link object: uHTR IP = {0}, n = {1}, status = {2}>".format(self.ip, self.n, "on" if self.on else "off")
		else:
			return "<empty link object>"
# /CLASSES

# FUNCTIONS:
def send_commands(ts=None, crate=None, slot=None, ip=None, control_hub=None, cmds=cmds_default, script=False):		# Sends commands to "uHTRtool.exe" and returns the raw output and a log. The input is a teststand object and a list of commands.
	# Arguments and variables:
	raw = ""
	results = {}		# Results will be indexed by uHTR IP unless a "ts" has been specified, in which case they'll be indexed by (crate, slot).
	
	## Parse ip argument:
	ips = meta.parse_args_ip(ts=ts, crate=crate, slot=slot, ip=ip)
	if ips:
		## Parse control_hub argument:
		control_hub = meta.parse_args_hub(ts=ts, control_hub=control_hub)
	
		## Parse cmds:
		if isinstance(cmds, str):
			print 'WARNING (uhtr.send_commands): You probably didn\'t intend to run "uHTRtool.exe" with only one command: {0}'.format(cmds)
			cmds = [cmds]
		cmds_str = ""
		for c in cmds:
			cmds_str += "{0}\n".format(c)
	
		# Send the commands:
		for uhtr_ip, crate_slot in ips.iteritems():
			# Prepare the uHTRtool arguments:
			uhtr_cmd = "uHTRtool.exe {0}".format(uhtr_ip)
			if control_hub:
				uhtr_cmd += " -o {0}".format(control_hub)
		
			# Send commands and organize results:
			if script:
				with open("uhtr_script.cmd", "w") as out:
					out.write(cmds_str)
#				print uhtr_cmd
				raw_output = Popen(['{0} < uhtr_script.cmd'.format(uhtr_cmd)], shell = True, stdout = PIPE, stderr = PIPE).communicate()
			else:
				raw_output = Popen(['printf "{0}" | {1}'.format(cmds_str, uhtr_cmd)], shell = True, stdout = PIPE, stderr = PIPE).communicate()		# This puts the output of the command into a list called "raw_output" the first element of the list is stdout, the second is stderr.
			raw += raw_output[0] + raw_output[1]
			if crate_slot:
				results[crate_slot] = raw
			else:
				results[uhtr_ip] = raw
		return results
	else:
		return False

def setup(ts=None, crate=None, slot=None, ip=None, control_hub=None, auto_realign=1, orbit_delay=3500):
# Set up any number of uHTRs. Specify a group of uHTRs by the crates and slots or by the IPs. If you specify the ts and nothing else it will set up all of them.
	# Arguments:
	ips = meta.parse_args_ip(ts=ts, crate=crate, slot=slot, ip=ip)
	if not ips:
		return False
	else:
		# Define setup commands:
		cmds = [
			"0",
			"clock",
			"setup",
			"3",
			"quit",
			"link",
			"init",
			"{0}".format(auto_realign),
			"{0}".format(orbit_delay),
			"0",
			"0",
			"0",
			"quit",
			"exit",
			"-1",
		]
		
		# Run setup commands:
		cs_exists = [bool(crate_slot) for ip, crate_slot in ips.iteritems()]
		if sum(cs_exists) == len(cs_exists):
			uhtr_out = send_commands(ts=ts, crate=crate, slot=slot, cmds=cmds)
		else:
			uhtr_out = send_commands(ip=ips.keys(), cmds=cmds, control_hub=control_hub)
		return uhtr_out

#def setup_links(ts=None, crate=None, slot=None, ip=None, control_hub=None, auto_realign=1, orbit_delay=59):
#	if ts:
#		# Parse crates and slots:
#		be = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot, crate_type="be")
#		if be:
#			# Define setup commands:
#			cmds = [
#				"0",
#				"link",
#				"init",
#				"1",		# Auto realign
#				"59",		# Orbit delay
#				"0",
#				"0",
#				"0",
#				"quit",
#				"exit",
#				"-1",
#			]
#		
#			# Run setup commands:
#			for crate, slots in be.iteritems():
#				for slot in slots:
#					output = send_commands(ts=ts, crate=crate, slot=slot, cmds=cmds)["output"]
#			sleep(1)		# Wait to give the links time to initialize.
#			return True
#		else:
#			print "ERROR (uhtr.setup_links): The crate, slot arguments were not good."
#			return False
#	else:
#		print "ERROR (uhtr.setup_links): You must supply a teststand argument!"
#		return False

def get_info(ts=None, crate=None, slot=None, ip=None, control_hub=None):		# Returns dictionaries of information about the uHTRs, such as the FW versions.
	# Arguments and variables:
	ips = meta.parse_args_ip(ts=ts, crate=crate, slot=slot, ip=ip)
	if not ips:
		return False
	else:
		data = {}
		
		# Get version info:
		## Run basic commands, which have version info in the output:
		cs_exists = [bool(crate_slot) for ip, crate_slot in ips.iteritems()]
		if sum(cs_exists) == len(cs_exists):
			uhtr_out = send_commands(ts=ts, crate=crate, slot=slot)
		else:
			uhtr_out = send_commands(ip=ips.keys(), control_hub=control_hub)
		for key, raw  in uhtr_out.iteritems():
			raw_output = raw
			
			## Find the version info from the raw output:
			## "HF-4800 (41) 00.0f.00" => FW = [00, 0f, 00], FW_type = [HF-4800, 41] (repeat for "back")
			match_front = search("Front Firmware revision : (HF-\d+|BHM) \((\d+)\) ([0-9a-f]{2})\.([0-9a-f]{2})\.([0-9a-f]{2})", raw_output)
			match_back = search("Back Firmware revision : (HF-\d+|BHM) \((\d+)\) ([0-9a-f]{2})\.([0-9a-f]{2})\.([0-9a-f]{2})", raw_output)
			if match_front and match_back:
				data[key] = {
					"fw_type_front": [match_front.group(1), int(match_front.group(2))],
					"fw_front": [int(match_front.group(3), 16), int(match_front.group(4), 16), int(match_front.group(5), 16)],
					"fw_type_back": [match_back.group(1), int(match_back.group(2))],
					"fw_back": [int(match_back.group(3), 16), int(match_back.group(4), 16), int(match_back.group(5), 16)],
				}
				data[key].update({
					"fws": [
						(
							"{0}.{1}".format(data[key]["fw_type_front"][0], data[key]["fw_type_front"][1]),
							"{0:03d}.{1:03d}.{2:03d}".format(data[key]["fw_front"][0], data[key]["fw_front"][1], data[key]["fw_front"][2])
						),
						(
							"{0}.{1}".format(data[key]["fw_type_back"][0], data[key]["fw_type_back"][1]),
							"{0:03d}.{1:03d}.{2:03d}".format(data[key]["fw_back"][0], data[key]["fw_back"][1], data[key]["fw_back"][2])
						),
					]
				})
			else:
				print "ERROR (uhtr.get_info): Failed to find all the FW versions in the raw data, which follows:\n{0}".format(raw_output)
				return False
		return data

def get_status(ts=None, crate=None, slot=None, ip=None, control_hub=None, ping=True):		# Perform basic checks with the uHTRTool.exe:
	# Arguments and variables:
	ips = meta.parse_args_ip(ts=ts, crate=crate, slot=slot, ip=ip)
	if not ips:
		return False
	else:
		statuses = {}
		for ip, crate_slot in ips.iteritems():
			s = status(ts=ts)
			if crate_slot:
				s.crate, s.slot = crate_slot
			
			# Ping uHTR IP:
			if ping:
				ping_result = Popen(["ping -c 1 {0}".format(ip)], shell = True, stdout = PIPE, stderr = PIPE).stdout.read()
				if ping_result:
					s.ip[ip] = 1
					s.status.append(1)
				else:
					s.ip[ip] = 0
					s.status.append(0)
			else:
				s.ip[ip] = -1
				s.status.append(-1)
			
			# Make sure the versions are accessible:
			if crate_slot:
				crate, slot = crate_slot
				uhtr_info = get_info(ts=ts, crate=crate, slot=slot)[crate_slot]
			else:
				uhtr_info = get_info(ip=ip, control_hub=control_hub)[ip]
			if uhtr_info:
				s.fws = uhtr_info["fws"]
				s.status.append(1)
			else:
				s.status.append(0)
			
			# Additional info:
			if crate_slot:
				crate, slot = crate_slot
				dump = get_dump(ts=ts, crate=crate, slot=slot)[crate_slot]
			else:
				dump = get_dump(ip=ip, control_hub=control_hub)[ip]
			s.dump = dump
			
			# Prepare what's returned:
			s.update()
			if crate_slot:
				statuses[crate_slot] = s
			else:
				statuses[ip] = s
		return statuses

## Parse raw uHTR output:
def parse_link_status(raw):		# Parses the raw ouput of the uHTRTool.exe's "LINK" > "STATUS".	
	# Variables:
	log = ""
	info = {}
	info["active"] = [0 for i in range(24)]		# There are 24 links per uHTR.
	info["orbit"] = [-1 for i in range(24)]		# There are 24 links per uHTR.
	
	# Parse active:
	n_times = 0
	for line in raw.split("\n"):
		if search("^BadCounter(\s*(X|ON)){12}", line):
			n_times += 1
			statuses_raw = line.replace("BadCounter", "").split()
			for i, status_raw in enumerate(statuses_raw):
				n_link = 12 * ((n_times - 1) % 2) + i
				if status_raw.strip() == "ON":
					info["active"][n_link] = 1
	if n_times < 2:
		log += ">> ERROR: No correct \"status\" was called on the link."
	elif n_times > 2:
		log += ">> ERROR: Hm, \"status\" was called on the link multiple times, so the active link list might be unreliable. (n_times = {0})".format(n_times)
	if (n_times % 2 != 0):
		log += ">> ERROR: Uh, there were an odd number of \"status\" lines, which is weird."
	
	# Parse orbit:
	n_times = 0
	for line in raw.split("\n"):
		if search("^OrbitRate\(kHz\)", line):
#			print line
			n_times += 1
			orbits_raw = line.replace("OrbitRate(kHz)", "").split()
			for i, orbit_raw in enumerate(orbits_raw):
				n_link = 12 * ((n_times - 1) % 2) + i
				info["orbit"][n_link] = float(orbit_raw)
	return info

## Get link information:
def get_info_links(ts=None, crate=None, slot=None, ip=None, control_hub=None, script=False):		# Statuses links and then returns a list of link indicies, for a certain uHTR.
	# Variables:
	log = ""
	link_info = {}
	
	# Get raw link information (LINK > STATUS):
	raw = get_raw_status(ts=ts, crate=crate, slot=slot, ip=ip, control_hub=control_hub, script=script)
	
	# Parse the information:
	for key, raw_output in raw.iteritems():
		link_info[key] = parse_link_status(raw_output)
	
	return link_info

def list_active_links(ts=None, crate=None, slot=None, ip=None, control_hub=None, port=ngfec.port_default, script=False):		# Returns a list of the indices of the active links for a particular set of uHTRs.
	# Variables:
	active_links = {}
	
	# Get link info:
	link_info = get_info_links(ts=ts, crate=crate, slot=slot, ip=ip, control_hub=control_hub, script=script)
	for key, info in link_info.iteritems():
		active_links[key] = [i_link for i_link, active in enumerate(info["active"]) if active]
	return active_links

## Get link objects:
def get_links(ts=None, crate=None, slot=None, ip=None, control_hub=None, port=ngfec.port_default):		# Fetches link objects for the links in specific uHTRs.
	# Parse crate, slot info:
	be = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot, crate_type="be")
	if be:
		# Set up the QIE card unique IDs if needed:
		if not qie.check_unique_id(ts=ts, crate=crate, slot=slot, control_hub=control_hub, port=port):
			is_set = qie.set_unique_id(ts=ts, crate=crate, slot=slot, control_hub=control_hub, port=port)
		else:
			is_set = True
		if is_set:
			results = {}
			# Get lists of the active links in the uHTRs in question:
			active_links = list_active_links(ts=ts, crate=crate, slot=slot, ip=ip, control_hub=control_hub, port=port)
			for be_crate, be_slots in be.iteritems():
				for be_slot in be_slots:
					crate_slot = (be_crate, be_slot)
					# For each active link, read QIE unique ID and fiber number from SPY data:
					# (self, uhtr_ip = "unknown", link_number = -1, qie_unique_id = "unknown", qie_half = -1, qie_fiber = -1, on = False)
					i_links_active = active_links[crate_slot]
					result = ts.set_mode(mode=2)		# Turn on test mode B.
					if result:
						links = []
						for i in range(24):		# Every uHTR has 24 possible links labeled 0 to 23.
							if i in i_links_active:
								data = get_data_spy(ts=ts, crate=be_crate, slot=be_slot, i_link=i)[crate_slot][i]		# Reading fewer than 50 "samples" sometimes results in no data ...
								if data:
#									print data
									qie_unique_id = "0x{0}{1} 0x{2}{3}".format(
										data[0][0].raw[4][1:5],		# This ordering is chosen to match the ngFEC tool's (MSB -> LSB)
										data[0][0].raw[3][1:5],
										data[0][0].raw[2][1:5],
										data[0][0].raw[1][1:5]
									).lower()
									qie_fiber = data[0][0].fiber
									qie_half = data[0][0].half
									links.append(link(
										ts=ts,
										be_crate=be_crate,
										be_slot=be_slot,
										link_number=i,
										qie_unique_id=qie_unique_id,
										qie_half=qie_half,
										qie_fiber=qie_fiber,
										on=True
									))
								else:
									links.append(link(
										ts=ts,
										be_crate=be_crate,
										be_slot=be_slot,
										on=True
									))
							else:
								links.append(link(
									ts=ts,
									be_crate=be_crate,
									be_slot=be_slot,
									link_number=i,
									on=False
								))
						results[(be_crate, be_slot)] = links
					else:
						print "ERROR (uhtr.get_links): Setting the teststand readout mode to Mode 2 failed."
						return False
			result = ts.set_mode(mode=0)		# Return the teststand to normal mode operation.
			return results
		else:
			print "ERROR (uhtr.get_links): The unique IDs couldn't be set."
			return False
	else:
		return False

def get_links_from_map(ts=None, crate=None, slot=None, end="be", i_link=None, f="", d="configuration/maps"):		# Returns a list of link objects configured with the data from the uhtr_map.
	# Arguments and variables:
	links = {}
	i_links = meta.parse_args_link(i_link=i_link)
	if not i_links: return False
	if end in ["be", "fe"]:
		end_name = end
		end = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot, crate_type=end_name)
		qie_map = ts.read_qie_map(f=f, d=d)
#		uhtr_info = ts.uhtr_from_qie()
		for crate, slots in end.iteritems():
			for slot in slots:
				crate_slot = (crate, slot)
				links[crate_slot] = []
				for i_link in i_links:
					qies = []
					for ch in range(4):
						qies.extend([i for i in qie_map if i["{0}_crate".format(end_name)] == crate and i["{0}_slot".format(end_name)] == slot and i["uhtr_link"] == i_link and i["uhtr_channel"] == ch])
					if len(qies) == 4:
						links[crate_slot].append(link(
							ts=ts,
							be_crate=qies[0]["be_crate"],
							be_slot=qies[0]["be_slot"],
							fe_crate=qies[0]["fe_crate"],
							fe_slot=qies[0]["fe_slot"],
							link_number=i_link,
							qie_unique_id=qies[0]["qie_id"],
							qie_half=qies[0]["uhtr_half"],
							qie_fiber=qies[0]["uhtr_fiber"],
							on=True,
							qies=[i["qie_n"] for i in qies]
						))
					elif len(qies) > 1:
						print "ERROR (get_link_from_map): More than one QIE in the map matches your criterion of crate = {0}, slot = {1}, and i_link = {2}.".format(be_crate, be_slot, i_link)
						return False
#					else:
#						print "WARNING (get_link_from_map): No QIE in the map matches your criterion of crate = {0}, slot = {1}, and i_link = {2}.".format(crate, slot, i_link)
#						links[crate_slot].append(link(
#							ts=ts,
#							link_number=i_link,
#							on=False,
#						))
		return links
	else:
		print "ERROR (uhtr.get_links_from_map): \"end\" must be either \"fe\" or \"be\"."
		return False

# calls the uHTRs histogramming functionality
# ip - ip address of the uHTR (e.g. teststand("904").uhtr_ips[0])
# n_orbits  - number of orbits to integrate over
# sepCapID - whether to distinguish between different cap IDs
# (currently I think this means you can only read out range 0)
# fileName - output file name
def get_histo(ts=False,crate=None, uhtr_slot=-1, n_orbits=1000, sepCapID=1, file_out=""):
	# Set up some variables:
	log = ""
	if not file_out:
		file_out = "histo_uhtr{0}.root".format(uhtr_slot)
	
	# Histogram:
	cmds = [
		'0',
		'link',
		'histo',
		'integrate',
		'{0}'.format(n_orbits),		# number of orbits to integrate over
		'{0}'.format(sepCapID),
		'{0}'.format(file_out),
		'0',
		'quit',
		'quit',
		'exit',
		'-1'
	]
	result = send_commands(ts=ts,crate=crate, slot=uhtr_slot, cmds=cmds)
	return file_out

def read_histo(file_in=""):
	result = []
	tf = TFile(file_in, "READ")
	tc = TCanvas("tc", "tc", 500, 500)
	for i_link in range(24):
			for i_ch in range(4):
				th = tf.Get("h{0}".format(4*i_link + i_ch))
				info = {}
				info["link"] = i_link
				info["channel"] = i_ch
				info["mean"] = th.GetMean()
				result.append(info)
	return result

# Perform basic uHTR commands:
## Returning raw output:
def get_raw_err(ts=None, crate=None, slot=None, ip=None, control_hub=None, script=False):
	cmds=[
		'0',
		'link',
		'errors',
		'1000',		# Number of ms
		'88000',
		'1',
		'1',
		'3500',
		'0',
		'0',
		'0',
		'quit',
		'exit',
		'-1',
		]
	result = send_commands(ts=ts, crate=crate, slot=slot, cmds=cmds, ip=ip, control_hub=control_hub, script=script)
	return result

def get_raw_spy(ts=None, crate=None, slot=None, ip=None, control_hub=None, script=False, n_bx=50, i_link=None):
	# Goal: return a list of raw SPY data indexed by crate_slot, then link number.

	# Arguments and variables:
	raw_spy = {}
	## Parse "i_link":
	i_links = meta.parse_args_link(i_link=i_link)
	
	for i_link in i_links:
		# Set up list of commands:
		cmds = [
			'0',
			'link',
			'spy',
			'{0}'.format(i_link),
			'0',
			'0',
			'{0}'.format(n_bx),
			'quit',
			'exit',
			'-1',
		]
		# Send commands:
		result = send_commands(ts=ts, crate=crate, slot=slot, cmds=cmds, ip=ip, control_hub=control_hub, script=script)
		if result:
			for key, raw_output in result.iteritems():
				if key not in raw_spy:
					raw_spy[key] = {}
				raw_spy[key][i_link] = raw_output
	return raw_spy

def get_raw_status(ts=None, crate=None, slot=None, ip=None, control_hub=None, script=False):
	# Variables:
	log = ""
	cmds = [
		'0',
		'link',
		'status',
		'quit',
		'exit',
		'-1',
	]
	
	# Send commands:
	result = send_commands(ts=ts, crate=crate, slot=slot, cmds=cmds, ip=ip, control_hub=control_hub, script=script)
	if result:
		return result
	else:
		return False

### get triggered data -
def get_triggered_data(ts=None, crate=None, slot=None, n_events=10, f="triggered_data", i_link=12, script=False):
	commands = [
		'0',
		'link',
#		'init',
#		'1',
#		'59',
#		'0',
#		'0',
#		'status',
		'l1acapture',
		'autorun',
		'{0}'.format(n_events),
		'5',
		'10',
		'0',
		'{0}'.format(f),
		'{0}'.format(i_link),
		'quit',
		'quit',
		'exit',
		'-1',
	]

	uhtr_out = send_commands(ts=ts, crate=crate, slot=slot, cmds=commands, script=script)
	return uhtr_out

# Parse uHTR output:
def parse_bxs(bxs=None):		# Decode using this format: https://svnweb.cern.ch/trac/cms-firmwsrc/browser/hcal/HF_RM_igloo2/trunk/HF_RM_igloo2/docs/HF_RM_DataFormat.txt#L25
	bxs_parsed = []
	for i_bx, bx in enumerate(bxs):
		# Not used: ['BCF8', '5508', '0901', '0BFF', 'FFFF', '0000']
		# Used: ['F8BC', '0855', '0109', 'FF0B', 'FFFF', '0000']
		# Set defaults:
		cid = [-1]*4
		adc = [-1]*4
		tdc_le = [-1]*4
		tdc_te = [-1]*4
		
		words = [word[2:] + word[:2] for word in bx]
		bytes = []
		for word in words:
			bytes.extend([word[:2], word[2:]])
#		print bytes		# ['BC', 'F4', '55', '03', '03', '02', '04', 'FF', 'FF', 'FF', '00', '00']
		
		# Decode CID:
		cid[0] = int(bytes[2][1], 16)%4
		cid[1] = int(bytes[2][1], 16)/4
		cid[2] = int(bytes[2][0], 16)%4
		cid[3] = int(bytes[2][0], 16)/4
		
		# Decode ADC:
		adc[0] = int(bytes[3], 16)
		adc[1] = int(bytes[4], 16)
		adc[2] = int(bytes[5], 16)
		adc[3] = int(bytes[6], 16)
		
		# Decode LE TDC:
		tdc_le[0] = int(bytes[9][1], 16)%4 + (int(bytes[8][1], 16)%4)*2**2 + (int(bytes[7][1], 16)%4)*2**4
		tdc_le[1] = int(bytes[9][1], 16)/4 + (int(bytes[8][1], 16)/4)*2**2 + (int(bytes[7][1], 16)/4)*2**4
		tdc_le[2] = int(bytes[9][0], 16)%4 + (int(bytes[8][0], 16)%4)*2**2 + (int(bytes[7][0], 16)%4)*2**4
		tdc_le[3] = int(bytes[9][0], 16)/4 + (int(bytes[8][0], 16)/4)*2**2 + (int(bytes[7][0], 16)/4)*2**4
		
		# Decode TE TDC:
		tdc_te[0] = int(bytes[10], 16)%8
		tdc_te[1] = int(bytes[10], 16)/8
		tdc_te[2] = int(bytes[11], 16)%8
		tdc_te[3] = int(bytes[11], 16)/8
		
		bx_parsed = []
		for ch in range(4):
			bx_parsed.append(qie.datum(
				ch=ch,
				bx=i_bx,
				raw=bx,
				cid=cid[ch],
				adc=adc[ch],
				tdc_le=tdc_le[ch],
				tdc_te=tdc_te[ch],
			))
		bxs_parsed.append(bx_parsed)
	return bxs_parsed

def parse_l1a(raw=None):
	# Parse something like this:
	#   0026 0F8BC 00000  CAP2   (<--- Triggered BX!)
	#   0028 00000 0FF00 ADC:   0   0   0   0   0 255
	#   0030 0FFFF 00000 TDC:  63  63  63   3   0   0
	#   0032 0F8BC 00855  CAP2   
	#   0034 00109 0FF0B ADC:  85   8   9   1  11 255
	#   0036 0FFFF 00000 TDC:  63  63  63   3   0   0
	#   0038 0F8BC 008AA  CAP2   
	#   0040 00000 0FF00 ADC: 170   8   0   0   0 255
	#   0042 0FFFF 00000 TDC:  63  63  63   3   0   0
	#   0044 0F8BC 000FF  CAP2   
	#   0046 00000 0FF00 ADC: 255   0   0   0   0 255
	#   0048 0FFFF 00000 TDC:  63  63  63   3   0   0

	# Get the words:
	events = []
	for raw_event in raw.split("N  RAW0  RAW1"):
#		print "-----"
#		print raw_event
		lines = raw_event.split("\n")
		lines_stripped = []
		for line in lines:
#			print line
			match = search("^\s*\d{4}\s+([0-9A-F]{5})\s+([0-9A-F]{5})", line)
#			print bool(match)
			if match:
				lines_stripped.append([match.group(1)[1:], match.group(2)[1:]])
		if lines_stripped:
#			print lines_stripped
			words_raw = [i for two_words in lines_stripped for i in two_words]
		#	words = [word[2:] + word[:2] for word in words_raw]		# This just adds confusion, I think.
			words = words_raw
	
			# Parse the words:
			if words[0][2:] == "BC":		# Must start at the beginning of a BX
				bxs = [words[i:i+6] for i in range(0, len(words), 6)]
				if len(bxs[-1]) != 6:		# Remove trailing incomplete BXs
					del bxs[-1]
				events.append(parse_bxs(bxs=bxs))
			else:
				print "ERROR (uhtr.parse_l1a): The data doesn't begin with a \"BC\", so it's hard to know where it starts."
#				return False
	return events

def parse_err(raw):
	bdr=[]
	raw=raw.values()[0].split('\n')
	for s in raw:
		if 'Status|' in s:
			stat=[st.strip() for st in s.split('|')[1:-1]]
		if "Bad" in s and "data" in s and "rate" in s:
			bdr.extend(s.split()[3:])
	err={}
	for i in range(24):
		if stat[i]=='ON':
			err[i]=float(bdr[i])
	return err

	
def parse_spy(raw):		# From raw uHTR SPY data, return a list of adcs, cids, etc. organized into sublists per fiber.
	# Variables:
	data = {
		"cid": [],
		"adc": [],
		"tdc": [],
		"raw": [],
	}
	
	# Extract the raw data lines from the raw uhtr input:
#	print raw
	raw_data = []
	for line in raw.split("\n"):
		if search("\s*\d+\s*[0-9A-F]{5}", line):
			raw_data.append(line.strip())
#	print raw_data
	
	# Put all the data in the data dictionary:
	raw_temp = []
	for line in raw_data:
#		print line
		cid_match = search("CAPIDS", line)
		if cid_match:
			data["cid"].append( [ int(i.replace("CAP","")) for i in line.split()[-2:] ][::-1] )		# This has to be reversed because the SPY prints the links out in reverse order.
		adc_match = search("ADC", line)
		if adc_match:
			data["adc"].append([int(i) for i in line.split()[-6:]][::-1])
		tdc_match = search("TDC", line)
		if tdc_match:
			data["tdc"].append([int(i) for i in line.split()[-6:]][::-1])
		raw_match = search("\d+\s+([0-9A-F]{5})\s*(.*)", line)
		if raw_match:
			raw_string = raw_match.group(1)
			raw_thing = raw_match.group(2)
			raw_temp.append(raw_string)
			if raw_thing:
				data["raw"].append(raw_temp)
				raw_temp = []
#	print data
	
	# Prepare the output:
	if not data["raw"]:
		return False
	else:
		# Format the data dictionary into datum objects:
#		print data
		results = [[] for i in range(6)]		# Will return a list of datum objects for each channel.
		for bx, adcs in enumerate(data["adc"]):
			for ch, adc in enumerate(adcs):
				results[ch].append(qie.datum(
					adc=adc,
					cid=data["cid"][bx][ch],
					tdc=data["tdc"][bx][ch],
					raw=data["raw"][bx],
					raw_uhtr=reduce(lambda x, y: x + "\n" + y, raw_data[bx*6:(bx + 1)*6]),		# The data for the relevant BX ...
					bx=bx,
					ch=ch,
				))
		return results

def get_data_spy(ts=None, crate=None, slot=None, ip=None, control_hub=None, script=False, n_bx=50, i_link=None):
	# Arguments and variables:
	data_spy = {}
	
	# Get raw data:
	raw_spy = get_raw_spy(ts=ts, crate=crate, slot=slot, ip=ip, control_hub=control_hub, n_bx=n_bx, i_link=i_link)
	if raw_spy:
		for key, raw_by_link in raw_spy.iteritems():
			for i, raw_output in raw_by_link.iteritems():
				if key not in data_spy:
					data_spy[key] = {}
				data_spy[key][i] = parse_spy(raw_output)
		return data_spy
	else:
		print "ERROR (uhtr.get_data_spy): Couldn't fetch SPY data from i_link = {0}".format(i_link)
		return False

def get_dump(ts=None, crate=None, slot=None, ip=None, control_hub=None):
# Set up any number of uHTRs. Specify a group of uHTRs by the crates and slots or by the IPs. If you specify the ts and nothing else it will set up all of them.
	# Arguments:
	ips = meta.parse_args_ip(ts=ts, crate=crate, slot=slot, ip=ip)
	if not ips:
		return False
	else:
		# Define setup commands:
		cmds = [
			"0",
			"LINK",
			"STATUS",
			"QUIT",
			"DTC",
			"STATUS",
			"QUIT",
			"LUMI",
			"QUIT",
			"DAQ",
			"STATUS",
			"QUIT",
			"EXIT",
			"-1",
		]
		
		# Run setup commands:
		cs_exists = [bool(crate_slot) for ip, crate_slot in ips.iteritems()]
		if sum(cs_exists) == len(cs_exists):
			uhtr_out = send_commands(ts=ts, crate=crate, slot=slot, cmds=cmds)
		else:
			uhtr_out = send_commands(ip=ips.keys(), cmds=cmds, control_hub=control_hub)
		return uhtr_out
# /FUNCTIONS
def get_linkdtc(ts, crate,uhtr_slot):
	log = ""
	crsl=(crate,uhtr_slot)
	commands = [
		"0",
		"LINK",
		"STATUS",
		"QUIT",
		"DTC",
		"STATUS",
		"QUIT",
		"EXIT",
		"-1"
	]
	
	uhtr_out = send_commands(ts=ts,crate=crate,slot=uhtr_slot, cmds=commands)[crsl]
	linkstatus=uhtr_out.split('> STATUS\n')[1].split(' \n\n\n   INIT')[0]
	dtcstatus=uhtr_out.split('================================================ ')[-1].split('\n\n   STATUS')[0]
	return (linkstatus+dtcstatus).replace('\n','\n{0}'.format(crsl))+'\n'

if __name__ == "__main__":
	print "Hang on."
	print 'What you just ran is "uhtr.py". This is a module, not a script. See the documentation ("readme.md") for more information.'
