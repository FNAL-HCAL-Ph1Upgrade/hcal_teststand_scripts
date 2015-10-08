from re import search, split
from subprocess import Popen, PIPE
import mch
import amc13
import glib
import uhtr
import ngccm
import ngfec
import qie
import bkp
import meta
import json
import os
import install

# CLASSES:
class teststand:
	# Construction:
	def __init__(self, name=None, f="teststands.txt", fe_crate=None, fe_slot=None, be_crate=None, be_slot=None):
		if name:
			self.name = name
			ts_info = {}
			
			# Extract teststand info from the teststand configuration file:
			ts_info = install.parse_ts_configuration(f)[self.name]

			if fe_crate:
				if isinstance(fe_crate, int):
					fe_crate = [fe_crate]
				ts_info["fe_crates"] = fe_crate
			if fe_slot:
				if isinstance(fe_slot, int):
					fe_slot = [[fe_slot]]
				ts_info["qie_slots"] = fe_slot
			if be_crate:
				if isinstance(be_crate, int):
					be_crate = [be_crate]
				ts_info["be_crates"] = be_crate
			if be_slot:
				if isinstance(be_slot, int):
					be_slot = [[be_slot]]
				ts_info["uhtr_slots"] = be_slot
#			print ts_info
			for key, value in ts_info.iteritems():
				setattr(self, key, value)
			if hasattr(self, "control_hub"):
				control_hub = self.control_hub
			else:
				control_hub = None
			
			# Assign a few other calculable attributes:
			self.fe = {}
			if len(self.fe_crates) <= len(self.qie_slots):
				for i in range(len(self.fe_crates)):
					self.fe[self.fe_crates[i]] = self.qie_slots[i]
			self.be = {}
			if len(self.be_crates) <= len(self.uhtr_slots):
				for i, be_crate in enumerate(self.be_crates):
					self.be[be_crate] = []
					uhtr_slots = self.uhtr_slots[i]
					for uhtr_slot in uhtr_slots:
						self.be[be_crate].append(uhtr_slot)
			self.uhtr_ips = {}
			for be_crate, be_slots in self.be.iteritems():
				for be_slot in be_slots:
					self.uhtr_ips[(be_crate, be_slot)] = "192.168.{0}.{1}".format(be_crate, 4*be_slot)
			
			# AMC13:
			self.amc13s = {}		# AMC13 objects indexed by the BE crate number.
			for i, ips in enumerate(self.amc13_ips):
				try:
					be_crate = self.be_crates[i]
				except:
					be_crate = self.be_crates[0]
				if ips:
					self.amc13s[be_crate] = amc13.amc13(
						ts=self,
						crate=be_crate,
						ip_t1=ips[0],
						ip_t2=ips[1],
						config="amc13_{0}_config.xml".format(self.name),
						i_sn = i,
					)
			
			# GLIB:
			self.glibs = {}		# GLIB objects indexed by the BE crate number.
			for i, glib_slots in enumerate(self.glib_slots):
				if glib_slots:
					try:
						be_crate = self.be_crates[i]
					except:
						be_crate = self.be_crates[0]
					self.glibs[be_crate] = []
					for glib_slot in glib_slots:
						self.glibs[be_crate].append(glib.glib(
							ts=self,
							crate=be_crate,
							slot=glib_slot,
							ip="192.168.1.{0}".format(160 + glib_slot),
						))
			
			# uHTRs:
			self.uhtrs = {}
			for be_crate, be_slots in self.be.iteritems():
				for be_slot in be_slots:
					self.uhtrs[(be_crate, be_slot)] = uhtr.uhtr(
						ts=self,
						crate=be_crate,
						slot=be_slot,
						ip="192.168.{0}.{1}".format(be_crate, 4*be_slot),
					)
			
			# BKP:
			self.bkps = {}		# Backplane objects indexed by the FE crate number.
			for i, crate in enumerate(self.fe_crates):
				self.bkps[crate] = bkp.bkp(
					ts=self,
					crate=crate,
				)
			
			# ngCCM:
			self.ngccms = {}		# ngCCM objects indexed by the FE crate number.
			for i, crate in enumerate(self.fe_crates):
				self.ngccms[crate] = ngccm.ngccm(
					ts=self,
					crate=crate,
				)
			
			# QIEs:
			self.qies = {}
			for fe_crate, fe_slots in self.fe.iteritems():
				for fe_slot in fe_slots:
					self.qies[(fe_crate, fe_slot)] = qie.qie(
						ts=self,
						crate=fe_crate,
						slot=fe_slot,
						control_hub=control_hub,
					)
			self.nqies = int(self.qie_cards_per_slot) * int(self.qies_per_card)

			self.uhtr = {}
			for slot in self.uhtr_slots[0]:
				ip = "192.168.{0}.{1}".format(self.be_crates[0], slot*4)
#					self.uhtr_ips.append(ip)
				self.uhtr[slot] = ip
			
#				self.glib_ip = "192.168.1.{0}".format(160 + self.glib_slot)
#			except Exception as ex:		# The above will fail if the teststand names doesn't appear in the configuration file.
#				print "ERROR: Could not read the teststand information for {0} from the configuration file: {1}".format(self.name, f)
#				print ">> {0}".format(ex)
		else:
			print "ERROR: You need to initialize a teststand object with a name (string) from the teststand configuration file (configuration/teststands.txt)."
	# /CONSTRUCTION
	
	# METHODS:
	## General:
	def update(self):
		results = []
		for be_crate, amc13 in self.amc13s.iteritems():
			results.append(amc13.update())
		for crate_slot, uhtr in self.uhtrs.iteritems():
			results.append(uhtr.update())
		for crate, ngccm in self.ngccms.iteritems():
			results.append(ngccm.update())
		for crate_slot, qie in self.qies.iteritems():
			results.append(qie.update())
#		print results
		if len(results) == sum(results):
			return True
		else:
			return False
	
	def Print(self, verbose=True):
		result = ""
		result += "######################################################\n"
		result += "# TESTSTAND {0}\n".format(self.name)
		result += "#\n"
		
		# Prepare BE stuff:
		result += "############### BE ###############\n"
		result += "# (uTCA crates: {0})\n".format(self.be_crates)
		for be_crate in self.be_crates:
			result += "### Crate {0}\n".format(be_crate)
			if be_crate in self.amc13s:		# There is only one possible per BE crate
				result += "# * AMC13s:\n"
				result += "#\t{0}\n".format(self.amc13s[be_crate])
			if be_crate in self.glibs:
				result += "# * GLIBs:\n"
				for glib in self.glibs[be_crate]:
					result += "#\t{0}\n".format(glib)
			uhtrs = [uhtr for crate_slot, uhtr in self.uhtrs.iteritems() if crate_slot[0] == be_crate]
#			print uhtrs
			if uhtrs:
				result += "# * uHTRs:\n"
				for uhtr in uhtrs:
					result += "#\t{0}\n".format(uhtr)
			result += "###\n"
		result += "##################################\n#\n"
		# Prepare FE stuff:
		result += "############### FE ###############\n"
		result += "# (FE crates: {0})\n".format(self.fe_crates)
		for fe_crate in self.fe_crates:
			result += "### Crate {0}\n".format(fe_crate)
			if fe_crate in self.bkps:		# There is only one possible per FE crate
				result += "# * Backplanes:\n"
				result += "#\t{0}\n".format(self.bkps[fe_crate])
			if fe_crate in self.ngccms:		# There is only one possible per FE crate
				result += "# * ngCCMs:\n"
				result += "#\t{0}\n".format(self.ngccms[fe_crate])
			qies = [qie for crate_slot, qie in self.qies.iteritems() if crate_slot[0] == fe_crate]
#			print uhtrs
			if qies:
				result += "# * QIE cards:\n"
				for qie in qies:
					result += "#\t{0}\n".format(qie)
			result += "###\n"
		result += "##################################\n"
		result += "######################################################"
		if verbose:
			print result
		return result
	
	## uHTR:
	def uhtr_ip(self, be_crate=None, be_slot=None):
		return self.uhtr_ips[(be_crate, be_slot)]
	
	def get_info_links(self, uhtr_slot=False):		# For each uHTR, returns a dictionary link status information.
		if uhtr_slot:
			uhtr_slots = uhtr_slot
		else:
			uhtr_slots = self.uhtr_slots
		
		result = {}
		for uhtr_slot in uhtr_slots:
			result[uhtr_slot] = uhtr.get_info_links(self, uhtr_slot)
		return result
	
	def list_active_links(self, uhtr_slot=False):		# For each uHTR, returns a list of the indices of the active links.
		if uhtr_slot:
			uhtr_slots = uhtr_slot
		else:
			uhtr_slots = self.uhtr_slots
		
		result = {}
		for uhtr_slot in uhtr_slots:
			result[uhtr_slot] = uhtr.list_active_links(self, uhtr_slot)
		return result
	
	def get_links(self, be_crate=None, be_slot=None, ip=None):
		return uhtr.get_links(ts=self, crate=be_crate, slot=be_slot, ip=ip)
	
	def get_links_from_map(self, be_crate=None, be_slot=None, i_link=None, f="", d="configuration/maps"):
		return uhtr.get_links_from_map(ts=self, crate=be_crate, slot=be_slot, i_link=i_link, f=f, d=d)
	
	## QIE:
	def set_ped(self, dac=None, dac_cid=None, i_qie=None, i_cid=set(range(4)), crate=None, slot=None):		# Set pedestal values.
		return qie.set_ped(ts=self, crate=crate, slot=slot, i_qie=i_qie, dac=dac, dac_cid=dac_cid, i_cid=i_cid)
	
	def set_fixed_range(self, enable=None, r=None, i_qie=None, crate=None, slot=None):		# Set fixed-range mode.
		return qie.set_fixed_range(ts=self, crate=crate, slot=slot, i_qie=i_qie, enable=enable, r=r)
	
	def set_clk_phase(self, crate=None, slot=None, i_qie=None, phase=0, script=True):		# Set QIE clock phase.
		return qie.set_clk_phase(ts=self, crate=crate, slot=slot, i_qie=i_qie, phase=phase, script=script)
	
	def set_ci(self, crate=None, slot=None, enable=False, script=True):		# Set charge-injection mode.
		return qie.set_ci(ts=self, crate=crate, slot=slot, enable=enable, script=script)
	
	def set_cal_mode(self, enable=False):
		for crate, slots in self.fe.iteritems():
			for slot in slots:
				qie.set_cal_mode_all(self, crate, slot, enable)
	
	## All:
	def set_mode(self, crate=None, slot=None, mode=0):
		return qie.set_mode(ts=self, crate=crate, slot=slot, mode=mode)
	
	def get_info(self):		# Returns a dictionary of component information, namely versions.
		data = {}
		data["amc13"] = amc13.get_info(ts=self)
		data["glib"] = glib.get_info(self)
		data["uhtr"] = uhtr.get_info(self)
		data["ngccm"] = []
		data["qie"] = []
		for crate, slots in self.fe.iteritems():
			data["ngccm"].append(ngccm.get_info(self, crate))
			for slot in slots:
				data["qie"].append(qie.get_info(self, crate, slot))
		return data
	
	def get_temps(self):		# Returns a list of various temperatures around the teststand.
		temps = []
		for i, crate in enumerate(self.fe_crates):
			temps.append(get_temp(self, crate, i)["temp"])		# See the "get_temp" funtion above.
		return temps
	
	def get_data(self, uhtr_slot=12, i_link=0, n=300):
		return uhtr.get_data_parsed(self, uhtr_slot, n, i_link)
	
	def get_status(self):		# Sets up and checks that the teststand is working.
		return get_ts_status(self)
	
	def get_qie_map(self):
		qie_map = qie.get_map_slow(self)
		return qie_map
	
	def save_qie_map(self, f="", d="configuration/maps"):		# Saves the qie map to a file named f in directory d.
		if f:
			if f.split(".")[-1] != "json":
				f += ".json"
		else:
			f = "{0}_qie_map.json".format(self.name)
		if not os.path.exists(d):
			os.makedirs(d)
		qie_map = self.get_qie_map()		# A qie map is from QIE crate, slot, qie number to link number, IP, unique_id, etc. It's a list of dictionaries with 3tuples as the keys: (crate, slot, qie)
		
#		qie_map_out = {}
#		for qie in qie_map:
#			qie_map_out["{0:02d}{1:02d}{2:02d}".format(qie["crate"], qie["slot"], qie["qie"])] = qie
		with open("{0}/{1}".format(d, f), "w") as out:
#			json.dump(qie_map_out, out)
			json.dump(qie_map, out)
	
	def read_qie_map(self, f="", d="configuration/maps"):
		if f:
			if f.split(".")[-1] != "json":
				f += ".json"
		else:
			f = "{0}_qie_map.json".format(self.name)
		
		path = d + "/" + f
		if os.path.exists(path):
			with open(path) as infile:
				qie_map = json.loads(infile.read())
		else:
			"ERROR: Could not find the qie_map at {0}".format(path)
			qie_map = []
		return qie_map
	
	def uhtr_from_qie(self, qie_id="", f="", d="configuration/maps"):
		result = {}
		qie_map = self.read_qie_map(f=f, d=d)
		if qie_id:
			uhtr_info = sorted(list(set([(qie["be_slot"], qie["uhtr_link"]) for qie in qie_map if qie["qie_id"] == qie_id])))
		else:
			uhtr_info = sorted(list(set([(qie["be_slot"], qie["uhtr_link"]) for qie in qie_map])))
#		print uhtr_info
		for slot, link in uhtr_info:
			if slot in result:
				result[slot].append(link)
			else:
				result[slot] = [link]
		return result

	def crate_slot_from_qie(self, qie_id="", f="", d="configuration/maps"):
		qie_map = self.read_qie_map(f=f, d=d)
		if qie_id:
			info = sorted(list(set([(qie["fe_crate"], qie["fe_slot"]) for qie in qie_map if qie["qie_id"] == qie_id])))
		else:
			info = sorted(list(set([(qie["fe_crate"], qie["fe_slot"]) for qie in qie_map])))
		if len(info) == 1:
			return info[0]
		else:
			print "WARNING (ts.crate_slot_from_qie): qie {0} maps to more than one crate, slot: {1}".format(qie_id, info)
			return info[0]
	
	def crate_slot_from_ip(self, ip=None):		# Useless ...
		if ip:
			for crate_slot, uhtr in self.uhtrs.iteritems():
				if uhtr.ip == ip:
					return crate_slot
			print "ERROR (hcal_teststand.crate_slot_from_ip): No BE crate and BE slot matched the IP address of {0}.".format(ip)
			return False
		else:
			print "ERROR (hcal_teststand.crate_slot_from_ip): You need to specify a uHTR IP address you want to map."
			return False
	
	def get_qies(self, unique_id, f="", d="configuration/maps"):
		return get_qies(self, unique_id, f=f, d=d)
	# /METHODS
	
	def __str__(self):		# This just defines what the object looks like when it's printed.
		if hasattr(self, "name"):
			return "<teststand object: {0}>".format(self.name)
		else:
			return "<empty teststand object>"
# /CLASSES

# FUNCTIONS:
def get_qies(ts, unique_id, f="", d="configuration/maps"):
	# Deal with QIE map location:
	if f:
		if f.split(".")[-1] != "json":
			f += ".json"
	else:
		f = "{0}_qie_map.json".format(ts.name)
	
	# Read the QIE map and construct qie objects:
	qie_map = ts.read_qie_map(f=f, d=d)
	qies = []
	for i_qie in [i_qie for i_qie in qie_map if i_qie["id"] == unique_id]:
		qies.append(qie.qie(
			ts=ts,
			unique_id=unique_id,
			crate=i_qie["crate"],
			slot=i_qie["slot"],
			n=i_qie["qie"],
			uhtr_slot=i_qie["uhtr_slot"],
			fiber=i_qie["fiber"],
			half=i_qie["half"],
			link=i_qie["link"],
			channel=i_qie["channel"],
		))
	return qies

# Return the temperatures of your system:
def get_temp(ts, crate, icrate):		# It's more flexible to not have the input be a teststand object. I should make it accept both.
	commands = []
	for slot in ts.qie_slots[icrate]:
		commands.append("get HE{0}-{1}-temperature_f".format(crate,slot))
		commands.append("wait")
	raw_output = ngccm.send_commands(ts, commands)["output"]
	temp = []
	log = []
	for i,slot in enumerate(ts.qie_slots[icrate]):
		temp.append("")
		log.append("")
		try:
			match = search("get HE{0}-{1}-temperature_f # ([\d\.]+)".format(crate, slot), raw_output)
			temp[i] = float(match.group(1))
		except Exception as ex:
			log[i] += 'Trying to find the temperature of Crate {0} with "{1}" resulted in: {2}\n'.format(crate, commands[i], ex)
			match = search("\n(.*ERROR!!.*)\n", raw_output)
		if match:
			log[i] += 'The data string was "{0}".'.format(match.group(0).strip())
	return {
		"temp":	temp,
		"log":	log,
		}

# THIS IS NOT GOING TO WORK, NEEDS TO BE UPDATED:
def get_temps(ts=False):		# It's more flexible to not have the input be a teststand object. I should make it accept both.
	output = {}
	
	if ts:
		for crate, slots in ts.fe.iteritems():
			output[crate] = []
			for slot in slots:
				cmds = [
					"get HE{0}-{1}-bkp_temp_f".format(crate, slot),		# The temperature sensor on the QIE card, near the bottom, labeled "U40".
				]
				output[crate] += ngfec.send_commands(ts=ts, cmds=cmds)
		return output
	else:
		return output

# Functions for the whole system (BE and FE):
def get_ts_status(ts):		# This function does basic initializations and checks. If all the "status" bits for each component are 1, then things are good.
	status = {}
	log = ""
	print ">> Checking the MCHs ..."
	status["mch"] = mch.get_status(ts)
	print ">> Checking the AMC13s ..."
	status["amc13"] = amc13.get_status(ts=ts)
	print ">> Checking the GLIBs ..."
	status["glib"] = glib.get_status(ts)
	print ">> Checking the uHTRs ..."
	status["uhtr"] = uhtr.get_status(ts)
	print ">> Checking the backplanes ..."
	status["bkp"] = ngccm.get_status_bkp(ts)
	print ">> Checking the ngCCMs ..."
	status["ngccm"] = ngccm.get_status(ts)
	print ">> Checking the QIE cards ..."
	status["qie"] = qie.get_status(ts)
	st = []
	for component in ["amc13", "glib", "mch", "uhtr", "bkp", "ngccm", "qie"]:
#		print component
		st_temp = 1
		for s in status[component]["status"]:
			if s != 1:
				st_temp = 0
		st.append(st_temp)
	return {
		"status": st,
		"info": status,
		"log": log,
	}
# /FUNCTIONS

# This is what gets exectuted when hcal_teststand.py is executed (not imported).
if __name__ == "__main__":
	print "Hang on."
	print 'What you just ran is "hcal_teststand.py". This is a module, not a script. See the documentation (readme.md) for more information.'
