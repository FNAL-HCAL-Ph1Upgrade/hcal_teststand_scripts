# This module contains functions for talking to the QIE card.

from re import search
from subprocess import Popen, PIPE
import ngfec
from time import time, sleep
from numpy import mean, std
import uhtr
import meta

# CLASSES:
class qie:
	# Construction:
	def __init__(self, ts=None, crate=None, slot=None, be_crate=None, be_slot=None, control_hub=None, port=ngfec.port_default, unique_id=None, fiber=-1, links=-1):
		self.qid = self.id = unique_id
		self.ts = ts
		self.crate = self.fe_crate = crate
		self.slot  = self.fe_slot = slot
		self.be_crate = be_crate
		self.be_slot = be_slot
		self.control_hub = control_hub
		self.port = port
		self.crate_slot = (crate, slot)
		self.fiber = fiber
		self.links = links
	
	# String behavior
	def __str__(self):
		try:
			return "<QIE card in FE Crate {0}, FE Slot {1}>".format(self.crate, self.slot)
		except Exception as ex:
#			print ex
			return "<empty qie object>"
	
	# Methods:
	def update(self):
		try:
			info = get_info(crate=self.crate, slot=self.slot, control_hub=self.control_hub, port=self.port)[(self.crate_slot)]
#			print info
			self.fw_igloo_top = info["fws"][0]
			self.fw_igloo_bot = info["fws"][1]
			self.fw_bridge = info["fws"][2]
			self.fws = info["fws"]
			if self.set_unique_id():
				return True
			else:
				return False
		except Exception as ex:
			print ex
			return False
	
	def Print(self):
		print self
	
	def setup(self, i_qie=None):
		return setup(crate=self.crate, slot=self.slot, i_qie=i_qie, control_hub=self.control_hub, port=self.port)["output"]
	
	def set_unique_id(self):
		unique_id = set_unique_id(crate=self.crate, slot=self.slot, control_hub=self.control_hub, port=self.port)[self.crate_slot]
		if unique_id:
			self.id = unique_id
			return True
		else:
			return False
	
	def check_unique_id(self, verbose=False):
		return check_unique_id(crate=self.crate, slot=self.slot, control_hub=self.control_hub, port=self.port, verbose=verbose)
	
	def get_data(self, n_bx=50, i_qie=None, from_map=True, method=0):		# Method 0 is for uHTR SPY. Nothing else is implemented, yet.
		# Arguments and variables:
		i_qie = meta.parse_args_qie(i_qie=i_qie)
		
		# Get the link objects corresponding to this QIE:
		if from_map:
			links = uhtr.get_links_from_map(ts=self.ts, crate=self.crate, slot=self.slot, end="fe")
			if links:
				links = [i for i in links[self.crate_slot] if i.on]		# Save only the active links.
			else:
				return False
		else:
			print "ERROR (qie.qie.get_data): Getting the links straight from the uHTR (from_map = {0}) isn't implemented, yet.".format(from_map)
			return False
		
		# Read data off of each link:
		data = {}		# Will be indexed by QIE number
		for link in links:
#			print link
			if method == 0:
				if set(link.qies) & set(i_qie):		# If the two sets intersect (have any common elements) ...
					result = link.get_data_spy(n_bx=n_bx)
					if result:
						for i, data_temp in zip(link.qies, result):
							if i in i_qie:
								data[i] = data_temp
					else:
						print "ERROR (qie.qie.get_data): Unable to get data from the links."
						return False
			else:
				print "ERROR (qie.qie.get_data): Could not get data because method value {0} wasn't recognized.".format(method)
				return False
		return data
	# /Methods

class datum:
	# Construction:
	def __init__(self, adc=-1, cid=-1, tdc=-1, raw=[], raw_uhtr="", bx=-1, ch=-1):
		self.adc = adc
		self.cid = cid
		self.tdc = tdc
		if not raw:
			raw = []
		self.raw = raw
		self.raw_uhtr = raw_uhtr
		self.bx = bx
		self.ch = ch
	
	# String behavior
	def __str__(self):
		if self.adc != -1:
			return "<qie.datum object: CID = {0}, ADC = {1}, TDC = {2} (CH{3})>".format(self.cid, self.adc, self.tdc, self.ch)
		else:
			return "<empty qie.datum object>"
	
	# Methods:
	def Print(self):
		print self
	# /Methods

class status:
	# Construction:
	def __init__(self, ts=None, status=[], crate=-1, slot=-1, id_top=[], id_bot=[], fw_top=[], fw_bot=[], fw_b=[]):
		if not ts:
			ts = None
		self.ts = ts
		if not status:
			status = []
		self.status = status
		self.crate = crate
		self.slot = slot
		if not id_top:
			id_top = []
		self.id_top = id_top
		if not id_bot:
			id_bot = []
		self.id_bot = id_bot
		if not fw_top:
			fw_top = []
		self.fw_top = fw_top
		if not fw_bot:
			fw_bot = []
		self.fw_bot = fw_bot
		if not fw_b:
			fw_b = []
		self.fw_b = fw_b
	
	# String behavior
	def __str__(self):
		if self.ts:
			return "<qie.status object: {0}>".format(self.status)
		else:
			return "<empty qie.status object>"
	
	# Methods:
	def update(self):
		self.good = (False, True)[bool(self.status) and len(self.status) == sum(self.status)]
	
	def Print(self, verbose=True):
		if verbose:
			print "[{0}] QIE card in Crate {1}, Slot {2} Status: {3} <- {4}".format(("!!", "OK")[self.good], self.crate, self.slot, ("BAD", "GOOD")[self.good], self.status)
			print "\tID IGLOO2 top: {0}".format(self.id_top)
			print "\tFW IGLOO2 top: {0}".format(self.fw_top)
			print "\tID IGLOO2 bottom: {0}".format(self.id_bot)
			print "\tFW IGLOO2 bottom: {0}".format(self.fw_bot)
			print "\tFW bridge: {0}".format(self.fw_b)
		else:
			print "[{0}] QIE card in Crate {1}, Slot {2} status: {3}".format(("!!", "OK")[self.good], self.crate, self.slot, ("BAD", "GOOD")[self.good])
	
	def log(self):
		output = "%% QIE {0}, {1}\n".format(self.crate, self.slot)
		output += "{0}\n".format(int(self.good))
		output += "{0}\n".format(self.status)
		output += "{0}\n".format(self.fw_top)
		output += "{0}\n".format(self.fw_bot)
		output += "{0}\n".format(self.fw_b)
		return output.strip()
	# /Methods
# /CLASSES

# FUNCTIONS:
def setup(ts=None, crate=None, slot=None, i_qie=None, control_hub=None, port=None, verbose=False):
# Set up any number of QIE cards. Specify a group of QIE cards by the crates and slots. If you specify the ts and nothing else, it will set up all of them.
	# Arguments:
	cmds = []
	## Parse "crate" and "slot"
	fe = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot, crate_type="fe")
	if fe:
		## Parse "i_qie":
		is_qie = meta.parse_args_qie(i_qie=i_qie)		# The default is range(1, 25)
		if is_qie:
			# Define setup commands:
			for fe_crate, slots in fe.iteritems():
				for fe_slot in slots:
#					print fe_crate, fe_slot
					for i_qie in is_qie:
						## Put all QIE program register values to default:
						cmds.extend([
							"put HF{0}-{1}-QIE{2}_Lvds 0x1".format(fe_crate, fe_slot, i_qie),		# 1 bit
							"put HF{0}-{1}-QIE{2}_Trim 0x2".format(fe_crate, fe_slot, i_qie),		# 2 bits
							"put HF{0}-{1}-QIE{2}_DiscOn 0x0".format(fe_crate, fe_slot, i_qie),		# 1 bit
							"put HF{0}-{1}-QIE{2}_TGain 0x0".format(fe_crate, fe_slot, i_qie),		# 1 bit
							"put HF{0}-{1}-QIE{2}_TimingThresholdDAC 0xff".format(fe_crate, fe_slot, i_qie),		# 8 bits
							"put HF{0}-{1}-QIE{2}_TimingIref 0x0".format(fe_crate, fe_slot, i_qie),		# 3 bits
							"put HF{0}-{1}-QIE{2}_PedestalDAC 0x26".format(fe_crate, fe_slot, i_qie),		# 6 bits
							"put HF{0}-{1}-QIE{2}_CapID0pedestal 0x0".format(fe_crate, fe_slot, i_qie),		# 4 bits
							"put HF{0}-{1}-QIE{2}_CapID1pedestal 0x0".format(fe_crate, fe_slot, i_qie),		# 4 bits
							"put HF{0}-{1}-QIE{2}_CapID2pedestal 0x0".format(fe_crate, fe_slot, i_qie),		# 4 bits
							"put HF{0}-{1}-QIE{2}_CapID3pedestal 0x0".format(fe_crate, fe_slot, i_qie),		# 4 bits
							"put HF{0}-{1}-QIE{2}_FixRange 0x0".format(fe_crate, fe_slot, i_qie),		# 1 bit
							"put HF{0}-{1}-QIE{2}_RangeSet 0x0".format(fe_crate, fe_slot, i_qie),		# 2 bits
							"put HF{0}-{1}-QIE{2}_ChargeInjectDAC 0x0".format(fe_crate, fe_slot, i_qie),		# 3 bits
							"put HF{0}-{1}-QIE{2}_RinSel 0x4".format(fe_crate, fe_slot, i_qie),		# 4 bits
							"put HF{0}-{1}-QIE{2}_Idcset 0x0".format(fe_crate, fe_slot, i_qie),		# 5 bits
							"put HF{0}-{1}-QIE{2}_CalMode 0x0".format(fe_crate, fe_slot, i_qie),		# 1 bit
							"put HF{0}-{1}-QIE{2}_CkOutEn 0x0".format(fe_crate, fe_slot, i_qie),		# 1 bit
							"put HF{0}-{1}-QIE{2}_TDCMode 0x0".format(fe_crate, fe_slot, i_qie),		# 1 bit
						])
						## Other QIE-specific things:
						cmds.extend([
							'put HF{0}-{1}-Qie{2}_ck_ph 0x0'.format(fe_crate, fe_slot, i_qie),		# Set the clock phase to 0.
						])
					## Put all other QIE card values to default values:
					cmds.extend([
						"put HF{0}-{1}-iTop_CntrReg_CImode 0x0".format(fe_crate, fe_slot),
						"put HF{0}-{1}-iBot_CntrReg_CImode 0x0".format(fe_crate, fe_slot),
#						"put HF{0}-{1}-iTop_LinkTestMode 0x0".format(fe_crate, fe_slot),
#						"put HF{0}-{1}-iBot_LinkTestMode 0x0".format(fe_crate, fe_slot),
						"put HF{0}-{1}-iTop_UniqueID 0x0 0x0".format(fe_crate, fe_slot),
						"put HF{0}-{1}-iBot_UniqueID 0x0 0x0".format(fe_crate, fe_slot),
					])
			if verbose: print "\tSetting all QIE chips and cards to default values ..."
			output = ngfec.send_commands(ts=ts, cmds=cmds, control_hub=control_hub, port=port, script=True)
			if output:
				if verbose: print "\tSetting QIE card IDs in the IGLOO registers ..."
				result = set_unique_id(ts=ts, crate=crate, slot=slot, control_hub=control_hub, port=port)
				if result:
					return {
						"output": output,
						"fe": fe,
						"ids": result,
					}
				else:
					if verbose: print "\tERROR (qie.setup): Failed to set up the QIE card IDs."
					return False
			else:
				return False
		else:
			return False
	else:
		return False

# Functions to fetch component information:
def get_info(ts=None, crate=None, slot=None, control_hub=None, port=ngfec.port_default, script=True):
	# Arguments and variables
	output = []
	raw_output = ""
	## Parse crate, slot:
	fe = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot, crate_type="fe")
	if fe:
		# Prepare:
		data = {}
		results = {}
		for crate, slots in fe.iteritems():
			for slot in slots:
				data[(crate, slot)] = []
				## Prepare bridge info:
				data[(crate, slot)].append([
					"fw_bridge_major",
					'get HF{0}-{1}-B_FIRMVERSION_MAJOR'.format(crate, slot),
				])
				data[(crate, slot)].append([
					"fw_bridge_minor",
					'get HF{0}-{1}-B_FIRMVERSION_MINOR'.format(crate, slot),
				])
				data[(crate, slot)].append([
					"fw_bridge_svn",
					'get HF{0}-{1}-B_FIRMVERSION_SVN'.format(crate, slot),
				])
				## Prepare IGLOO info:
				data[(crate, slot)].append([
					"fw_igloo_top_major",
					'get HF{0}-{1}-iTop_FPGA_MAJOR_VERSION'.format(crate, slot),
				])
				data[(crate, slot)].append([
					"fw_igloo_top_minor",
					'get HF{0}-{1}-iTop_FPGA_MINOR_VERSION'.format(crate, slot),
				])
				data[(crate, slot)].append([
					"fw_igloo_bot_major",
					'get HF{0}-{1}-iBot_FPGA_MAJOR_VERSION'.format(crate, slot),
				])
				data[(crate, slot)].append([
					"fw_igloo_bot_minor",
					'get HF{0}-{1}-iBot_FPGA_MINOR_VERSION'.format(crate, slot),
				])
				data[(crate, slot)].append([
					"id_igloo_top",
					'get HF{0}-{1}-iTop_UniqueID'.format(crate, slot),
				])
				data[(crate, slot)].append([
					"id_igloo_bot",
					'get HF{0}-{1}-iBot_UniqueID'.format(crate, slot),
				])
		# Compile list of commands to send:
		cmds = [d[1] for crate_slot, ds in data.iteritems() for d in ds]
#		print cmds
		# Send commands:
		ngfec_out = ngfec.send_commands(ts=ts, cmds=cmds, control_hub=control_hub, port=port, script=script)
		# Understand results:
		for crate_slot, ds in data.iteritems():
			results[crate_slot] = {}
			for i, d in enumerate(ds):
				key = d[0]
				cmd = d[1]
				for result in ngfec_out:
					if result["cmd"] == cmd:
						if "ERROR" not in result["result"]:
							if "UniqueID" not in cmd:
								results[crate_slot].update({
									key: int(result["result"], 16)
								})
							else:
								results[crate_slot].update({
									key: result["result"].split()
								})
						else:
							results[crate_slot].update({
								key: False
							})
			results[crate_slot]["fws"] = [
				"{0:02d}.{1:02d}".format(results[crate_slot]["fw_igloo_top_major"], results[crate_slot]["fw_igloo_top_minor"]),
				"{0:02d}.{1:02d}".format(results[crate_slot]["fw_igloo_bot_major"], results[crate_slot]["fw_igloo_bot_minor"]),
				"{0:02d}.{1:02d}.{2:04d}".format(results[crate_slot]["fw_bridge_major"], results[crate_slot]["fw_bridge_minor"], results[crate_slot]["fw_bridge_svn"]),
			]
		# Return results:
		return results
	else:
		return False

def get_unique_id(ts=None, crate=None, slot=None, control_hub=None, port=ngfec.port_default, script=False):		# Reads the unique ID of a given set of crates and slots.
	# INFO: "get HF1-1-UniqueID # '1 0x5f000000 0x9b46ce70'"
	# Arguments:
	## Parse "crate" and "slot"
	fe = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot, crate_type="fe")
	if fe:
#		cmds = []
		results = {}
		# Get the unique ID for each crate, slot
		for crate, slots in fe.iteritems():
			for slot in slots:
#				cmds=.append("get HF{0}-{1}-UniqueID".format(crate, slot))
				output = ngfec.send_commands(ts=ts, cmds=["get HF{0}-{1}-UniqueID".format(crate, slot)], control_hub=control_hub, port=port, script=script)
				if output:
					crate_slot = (crate, slot)
					result = output[0]["result"]
					if "ERROR" not in result:
						results[crate_slot] = result.split()[1:3]		# The first element doesn't matter.
					else:
						results[crate_slot] = False
				else:
					return False
		return results
	else:
		return False

def get_map(ts, v=False):		# Determines the QIE map of the teststand. A qie map is from QIE crate, slot, qie number to link number, IP, unique_id, etc. It's a list of dictionaries with 3tuples as the keys: (crate, slot, qie)
	# THIS IS A WORK IN PROGRESS. Use get_map_slow until this is fixed.
	print ">> Getting links ..."
	links_by_slot = ts.get_links()
	qie_map = []
	
	# Make sure the teststand is set up:
	print "Disabling fixed-range mode ..."
	ts.set_fixed_range(enable=False)
	
	# Do the mapping:
	for crate, slots in ts.fe.iteritems():
		for slot in slots:
			print ">> Mapping crate {0}, slot {1} ...".format(crate, slot)
			for i in range(2):		# Do the following step twice (for QIEs 1-12, and for 13-24).
				print ">> Doing the cycle {0} ...".format(i)
				uhtr_data = []
				ts.set_fixed_range(enable=False, crate=crate, slot=slot)		# Disable fixed-range mode for the card.
				for qie in range(i*12 + 1, i*12 + 13):
					if (v): print "{0} -> {1}".format(qie, int((qie - i*12 - 1)/4) + 1)
					set_fix_range(ts, crate, slot, qie, True, int((qie - i*12 - 1)/4) + 1)
				files_histo = {}
				for uhtr_slot in links_by_slot.keys():
					files_histo[uhtr_slot] = uhtr.get_histo(ts=ts, uhtr_slot=uhtr_slot, sepCapID=0)
					uhtr_data_temp = uhtr.read_histo(files_histo[uhtr_slot])
					temp = {}
					for datum in uhtr_data_temp:
						temp = datum
						temp["uhtr_slot"] = uhtr_slot
						uhtr_data.append(temp)
				
				groups = [[] for j in range(4)]
				for r in range(1, 4):
					for datum in uhtr_data:
						if datum["mean"] > r*64 - 10 and datum["mean"] < r*64 + 10:
#							print datum["mean"]
							groups[r].append(datum)
				
				for r in range(4):
					if len(groups[r]) == 4:
						if len([j["link"] for j in groups[r]]) == 1 and len([j["uhtr_link"] for j in groups[r]]) == 1:
							i_link = groups[r][0]["link"]
							uhtr_slot = groups[r][0]["uhtr_slot"]
						else:
							print "ERROR (qie.get_map): Something is strange about how things are organized ..."
							print groups[r]
					else:
						print "ERROR (qie.get_map): The following group doesn't contain four QIEs"
						print groups[r]
	
	# Make sure the teststand is set up:
	print "Disabling fixed-range mode ..."
	for crate, slots in ts.fe.iteritems():
		for slot in slots:
			set_fix_range_all(ts, crate, slot, False)
	
	return qie_map

def get_map_slow(ts):		# Determines the QIE map of the teststand. A qie map is from QIE crate, slot, qie number to link number, IP, unique_id, etc. It's a list of dictionaries with 3tuples as the keys: (crate, slot, qie)
	print "> Getting links ..."
	link_dict = ts.get_links()
	qie_map = []
	
	# Make sure the teststand is set up:
	print "> Disabling fixed-range mode ..."
	ts.set_fixed_range(enable=False)
	
	# Do the mapping:
	for fe_crate, fe_slots in ts.fe.iteritems():
		for fe_slot in fe_slots:
#			ts.set_fixed_range(crate=crate, slot=slot, enable=False)
			for i_qie in range(1, 25):
				print "> Finding FE crate {0}, FE slot {1}, QIE {2} ...".format(fe_crate, fe_slot, i_qie)
				ts.set_fixed_range(crate=fe_crate, slot=fe_slot, i_qie=i_qie, enable=True, r=2)
				channel_save = []
				link_save = []
				for be_crate_slot, links in link_dict.iteritems():
					be_crate, be_slot = be_crate_slot
					for link in [l for l in links if l.on]:
						data = link.get_data_spy()
						if data:
							for channel in range(4):
								adc_avg = mean([d.adc for d in data[channel]])
								print adc_avg
								if adc_avg == 128:
									channel_save.append(channel)
									link_save.append(link)
						else:
							print "ERROR (qie.get_map_slow): Data couldn't be read from the link."
				if len(channel_save) == 1 and len(link_save):
					channel = channel_save[0]
					link = link_save[0]
					qie_map.append({
						"be_crate": be_crate,
						"be_slot": be_slot,
						"fe_crate": fe_crate,
						"fe_slot": fe_slot,
						"qie_n": i_qie,
						"qie_id": link.qie_unique_id,
						"uhtr_link": link.n,
						"uhtr_channel": channel,
						"uhtr_half": link.qie_half,
						"uhtr_fiber": link.qie_fiber,
					})
				else:
					if len(channel_save) > 1:
						print "ERROR: Mapping is weird."
					qie_map.append({
						"be_crate": [link.crate for link in link_save],
						"be_slot": [link.slot for link in link_save],
						"fe_crate": fe_crate,
						"fe_slot": fe_slot,
						"qie_n": i_qie,
						"qie_id": [link.qie_unique_id for link in link_save],
						"uhtr_link": [link.n for link in link_save],
						"uhtr_channel": channel_save,
						"uhtr_half": [link.qie_half for link in link_save],
						"uhtr_fiber": [link.qie_fiber for link in link_save],
					})
				ts.set_fixed_range(crate=fe_crate, slot=fe_slot, i_qie=i_qie, enable=False)
	return qie_map
# /

# Functions dealing with QIE card unique ID:
def set_unique_id(ts=None, crate=None, slot=None, control_hub=None, port=ngfec.port_default):		# Saves the unique ID of the QIE card in crate, slot to IGLOO registers.
	#Arguments:
	## Parse "crate" and "slot"
	fe = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot, crate_type="fe")
	if fe:
		unique_ids = get_unique_id(ts=ts, crate=crate, slot=slot, control_hub=control_hub, port=port)
		if unique_ids:
			cmds = []
			for crate_slot, unique_id in unique_ids.iteritems():
				if unique_id:
					cmds.extend([
						"put HF{0}-{1}-iTop_UniqueID {2} {3}".format(crate_slot[0], crate_slot[1], unique_id[0], unique_id[1]),
						"put HF{0}-{1}-iBot_UniqueID {2} {3}".format(crate_slot[0], crate_slot[1], unique_id[0], unique_id[1])
					])
				else:
					print "ERROR (set_unique_id): The unique ID for the card in FE Crate {0}, Slot {1} could not be fetched. Therefore, it can't be set.".format(crate_slot[0], crate_slot[1])
					return False
			output = ngfec.send_commands(ts=ts, cmds=cmds, control_hub=control_hub, port=port)
			if output:
				return unique_ids
			else:
				return False
		else:
			return False
	else:
		return False

## Check to see if the QIE card unique IDs have been set in the IGLOO registers.
def check_unique_id(ts=None, crate=None, slot=None, control_hub=None, port=ngfec.port_default, verbose=False):
	#Arguments:
	## Parse "crate" and "slot"
	fe = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot, crate_type="fe")
	if fe:
		# Get the unique ID values:
		cmds = []
		for fe_crate, fe_slots in fe.iteritems():
			for fe_slot in fe_slots:
				cmds.extend([
					"get HF{0}-{1}-iTop_UniqueID".format(fe_crate, fe_slot),
					"get HF{0}-{1}-iBot_UniqueID".format(fe_crate, fe_slot),
				])
		results = ngfec.send_commands(ts=ts, cmds=cmds, control_hub=control_hub, port=port)
		
		# Check the unique ID values:
		if results:
			good = []
			values_previous = []
			for i, result in enumerate(results):
				values = [int(j, 16) for j in result["result"].split()]
#				values = [int(j, 16) for j in "0 0xbad".split()]
#				print values
				if len(values) == 2 and 0 not in values:
					if i%2 == 1:
						if values == values_previous:
							good.append(True)
						else:
#							print values, values_previous
							good.append(False)
					else:
						good.append(True)
				else:
					good.append(False)
				values_previous = values
			if sum(good) == len(good) and len(good) > 0:
				if verbose: print "[OK] The unique IDs were all set properly:\n{0}".format(results)
				return True
			else:
				if verbose: print "[!!] The unique IDs were not all set properly:\n{0}".format(results)
				return False
		else:
			return False
	else:
		return False
# /

# Functions to "status" components, including calculating clocks:
def get_status(ts=None, crate=None, slot=None, control_hub=None, port=ngfec.port_default):		# Perform basic checks of the QIE cards:
	# Arguments and variables:
	log =""
	## Parse "crate" and "slot"
	fe = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot, crate_type="fe")
	if fe:
		statuses = {}
		qie_info = get_info(ts=ts, crate=crate, slot=slot, control_hub=control_hub, port=port)
		for crate, slots in fe.iteritems():
			for slot in slots:
				crate_slot = (crate, slot)
				s = status(ts=ts, crate=crate, slot=slot)
				# IGLOO top status:
				s.id_top = qie_info[crate_slot]["id_igloo_top"]
				s.fw_top = [
					qie_info[crate_slot]["fw_igloo_top_major"],
					qie_info[crate_slot]["fw_igloo_top_minor"],
				]
				if sum(s.fw_top) >= 2 and sum([i !="0" for i in s.id_top]) == 2:
					s.status.append(1)
				else:
					s.status.append(0)
				
				# IGLOO bottom status:
				s.id_bot = qie_info[crate_slot]["id_igloo_bot"]
				s.fw_bot = [
					qie_info[crate_slot]["fw_igloo_bot_major"],
					qie_info[crate_slot]["fw_igloo_bot_minor"],
				]
				if sum(s.fw_bot) >= 2 and sum([i !="0" for i in s.id_bot]) == 2:
					s.status.append(1)
				else:
					s.status.append(0)
				
				# Bridge status:
				s.fw_b = [
					qie_info[crate_slot]["fw_bridge_major"],
					qie_info[crate_slot]["fw_bridge_minor"],
					qie_info[crate_slot]["fw_bridge_svn"],
				]
				if sum(s.fw_b) >= 3:
					s.status.append(1)
				else:
					s.status.append(0)
				
		#		# Check QIE resets in the BRIDGE (1) and the IGLOO2s (2):
		#		orbit_temp = []
		#		f_orbit_bridge = f_orbit["bridge"][i_qie]
		#		f_orbit_igloo = f_orbit["igloo"][i_qie]
		#		## (1) Check the BRIDGE:
		#		if (f_orbit_bridge["f"] < 13000 and f_orbit_bridge["f"] > 10000 and f_orbit_bridge["f_e"] < 500):
		#			status["status"].append(1)
		#		else:
		#			status["status"].append(0)
		#		orbit_temp.append([f_orbit_bridge["f"], f_orbit_bridge["f_e"]])
		#		## (2) Check the IGLOO2s:
		#		for i in range(2):
		#			if (f_orbit_igloo["f"][i] < 13000 and f_orbit_igloo["f"][i] > 10000 and f_orbit_igloo["f_e"][i] < 600):
		#				status["status"].append(1)
		#			else:
		#				status["status"].append(0)
		#			orbit_temp.append([f_orbit_igloo["f"][i], f_orbit_igloo["f_e"][i]])
		#		status["orbit"].append(orbit_temp)
				
				s.update()
				statuses[crate_slot] = s
		return statuses
	else:
		return False

def get_status_all(ts=None):
	log = ""
	ss = []
	
	if ts:
		for crate, slots in ts.fe.iteritems():
			for slot in slots:
				ss.append(get_status(ts=ts, crate=crate, slot=slot))
	return ss

def read_counter_qie_bridge(ts, crate, slot):
	log = ""
	count = -1
	cmd = "get HF{0}-{1}-B_RESQIECOUNTER".format(crate, slot)
	output = ngfec.send_commands(ts=ts, cmds=cmds)
	try:
		count = int(output[0]["result"], 16)
	except Exception as ex:
		log += output[0]["cmd"] + " -> " + output[0]["result"] + "\n"
	return {
		"count": count,
		"log": log,
	}

def read_counter_qie_igloo(ts, crate, slot):
	log = ""
	counts = [-1, -1]
	times = [-1, -1]
	cmds = [
		"get HF{0}-{1}-iTop_RST_QIE_count".format(crate, slot),
		"get HF{0}-{1}-iBot_RST_QIE_count".format(crate, slot),
	]
	output = ngfec.send_commands(ts=ts, cmds=cmds)
	for i in range(2):
		try:
			counts[i] = int(output[i]["result"], 16)
			times[i] = output[i]["times"][0]
		except Exception as ex:
			log += output[i][0] + " -> " + output[i][1] + "\n" + ex + "\n"
	return {
		"counts": counts,
		"times": times,
		"log": log,
	}

def get_frequency_orbit(ts):
	data = {
		"bridge": [],
		"igloo": [],
		"log": "",
	}
	for crate, slots in ts.fe.iteritems():
		for slot in slots:
			for fpga in data.keys():
				if fpga == "bridge":
					c = []
					t = []
					for i in range(6):
						result = read_counter_qie_bridge(ts, crate, slot)
						data["log"] += result["log"]
						c.append(result["count"])
						t.append(time())
#						sleep(0.01)
					f = []
					for i in range(len(c)-1):
						f.append((c[i+1]-c[i])/(t[i+1]-t[i]))
					data[fpga].append({
						"f_list":	f,
						"f":	mean(f),
						"f_e":	std(f)/(len(f)**0.5),
					})
				elif fpga == "igloo":
					c = []
					t = []
					for i in range(6):
						result = read_counter_qie_igloo(ts, crate, slot)
						data["log"] += result["log"]
						c.append(result["counts"])
						t.append([result["times"][0], result["times"][1]])
#						sleep(0.01)
					f = []
					for j in range(2):
						f_temp = []
						for i in range(len(c)-1):
							f_temp.append((c[i+1][j]-c[i][j])/(t[i+1][j]-t[i][j]))
						f.append(f_temp)
					data[fpga].append({
						"f_list":	f,
						"f":	[mean(f[0]), mean(f[1])],
						"f_e":	[std(f[0])/(len(f[0])**0.5), std(f[1])/(len(f[1])**0.5)],
					})
	return data
# /

# Functions to set IGLOO settings:
## Set IGLOO readout mode:
def set_mode(ts=None, crate=None, slot=None, mode=0, control_hub=None, port=ngfec.port_default, verbose=False):		# 0: normal mode, 1: link test mode A (test mode string), 2: link test mode B (IGLOO register)
	# Parse "crate" and "slot":
	fe = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot)
	if fe:
		# Parse "mode":
		if mode == 0:
			n = 0
		elif mode == 1:
			n = 1
		elif mode == 2:
			n = 7
		else:
			print "ERROR (qie.set_mode): I don't understand mode = {0}.".format(mode)
			return False
		
		# Build command list:
		cmds = []
		for crate, slots in fe.iteritems():
			for slot in slots:
				cmds.extend([
					"put HF{0}-{1}-iTop_LinkTestMode 0x{2}".format(crate, slot, n),
					"put HF{0}-{1}-iBot_LinkTestMode 0x{2}".format(crate, slot, n),
					"get HF{0}-{1}-iTop_LinkTestMode".format(crate, slot),
					"get HF{0}-{1}-iBot_LinkTestMode".format(crate, slot),
				])
		
		# Send commands:
		output = ngfec.send_commands(ts=ts, cmds=cmds, control_hub=control_hub, port=port)
		results = ["ERROR" not in j for j in [i["result"] for i in output]]
		if sum(results) == len(results):
			if verbose:
				for thing in output:
					print "\t{0} -> {1}".format(thing["cmd"], thing["result"])
			if uhtr.setup(ts=ts):		# This initializes all uHTRs' links. This is necessary after changing modes.
				return True
			else:
				print "ERROR (qie.set_mode): Reinitializing the uHTR links failed."
				return False
		else:
			print "ERROR (qie.set_mode): Setting the mode resulted in the following:"
			for thing in output:
				print "\t{0} -> {1}".format(thing["cmd"], thing["result"])
			return False
	else:
		print "ERROR (qie.set_mode): The crate, slot arguments were not good."
		return False
## /

## Set charge inject (CI) mode:
def set_ci(ts=None, crate=None, slot=None, enable=False, control_hub=None, script=False):
	# Parse "crate" and "slot":
	fe = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot)
	if fe:
		# Parse enable:
		if enable:
			enable_cmd = 1
		else:
			enable_cmd = 0
		
		# Build command list:
		cmds = []
		for crate, slots in fe.iteritems():
			for slot in slots:
				cmds.extend([
					"put HF{0}-{1}-iTop_CntrReg_CImode 0x{2}".format(crate, slot, enable_cmd),
					"put HF{0}-{1}-iBot_CntrReg_CImode 0x{2}".format(crate, slot, enable_cmd),
				])
		
		# Send commands:
		output = ngfec.send_commands(ts=ts, cmds=cmds, control_hub=control_hub, script=script)
		results = ["ERROR" not in j for j in [i["result"] for i in output]]
		if sum(results) == len(results):
			return output
		else:
			print "ERROR (qie.set_ci): Setting the mode resulted in the following:"
			for thing in output:
				print "\t{0} -> {1}".format(thing["cmd"], thing["result"])
			return False
	else:
		print "ERROR (qie.set_ci): The crate, slot arguments were not good."
		return False
## /
# /

# Functions to set QIE registers:
## Pedestals:
def set_ped(ts=False, crate=None, slot=None, i_qie=None, dac=None, dac_cid=None, i_cid=set(range(4)), control_hub=None, port=ngfec.port_default):		# Set the pedestal of QIE "i_qie" to DAC value "dac" and CID DAC value of "dac_cid".
	# Parse "crate" and "slot":
	fe = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot)
	if fe:
		# Parse "i_qie":
		i_qie = meta.parse_args_qie(i_qie=i_qie)		# The default is range(1, 25)
		if i_qie:
			# Parse "i_cid":
			i_cid_original = i_cid
			if isinstance(i_cid, int):
				i_cid = [i_cid]
			elif not (isinstance(i_cid, list) or isinstance(i_cid, set)):
				print "ERROR (qie.set_ped): You must enter an integer or a list of integers for \"i_cid\". The pedestals have not be changed."
				return False
			i_cid = set(i_cid)
			if not i_cid.issubset(set(range(4))):
				print "ERROR (qie.set_ped): \"i_cid\" can only contain elements of [0, 1, 2, 3], but you tried to set it to {0}. The pedestals have not be changed.".format(i_cid_original)
				return False
		
			# Parse "dac" and "dac_cid":
			if dac == None and dac_cid == None:
				print "WARNING (qie.set_ped): You didn't supply a \"dac\" or \"dac_cid\", so \"dac\" will be set to 6, the default, and \"dac_cid\" will be set to 0, the default, for all \"i_cid\" in {0} and all \"i_qie\" in {1}.".format(i_cid, i_qie)
				dac = 6
				dac_cid = 0
		
			## Parse "dac":
			if dac != None:
				if abs(dac) > 31:
					print "ERROR (qie.set_ped): You must enter a decimal integer for \"dac\" between -31 and 31. You tried to set it to {0}. The pedestals have not been changed.".format(dac)
					return False
				else:
					if dac <= 0:
						dac = abs(dac)
					else:
						dac = dac + 32
					dac_str = "{0:#04x}".format(dac)		# The "#" prints the "0x". The number of digits to pad with 0s must include these "0x", hence "4" instead of "2".
			else:
				dac_str = False
		
			## Parse "dac_cid":
			if dac_cid != None:
				if abs(dac_cid) > 7:
					print "ERROR (qie.set_ped): You must enter a decimal integer for \"dac_cid\" between -7 and 7. You tried to set it to {0}. The pedestals have not been changed.".format(dac_cid)
					return False
				else:
					if dac_cid <= 0:
						dac_cid = abs(dac_cid)
					else:
						dac_cid = dac_cid + 8
					dac_cid_str = "{0:#04x}".format(dac_cid)		# The "#" prints the "0x". The number of digits to pad with 0s must include these "0x", hence "4" instead of "2".
			else:
				dac_cid_str = False
		
			# See where things stand:
			if not dac_str and not dac_cid_str:
				print "ERROR (qie.set_ped): You intended to set pedestals, but it turns out none will be changed."
				return False
			if not fe:
				print "ERROR (qie.set_ped): The crate/slot configuration is all jacked up."
				return False
		
			# Build command list:
			cmds = []
			for crate, slots in fe.iteritems():
				for slot in slots:
					for i in i_qie:
						if dac_str:
							cmds.extend([
								"put HF{0}-{1}-QIE{2}_PedestalDAC {3}".format(crate, slot, i, dac_str),
								"get HF{0}-{1}-QIE{2}_PedestalDAC".format(crate, slot, i),
							])
						if dac_cid_str:
							for j in i_cid:
								cmds.extend([
									"put HF{0}-{1}-QIE{2}_CapID{3}pedestal {4}".format(crate, slot, i, j, dac_cid_str),
									"get HF{0}-{1}-QIE{2}_CapID{3}pedestal".format(crate, slot, i, j),
								])
	
			# Send commands:
			output = ngfec.send_commands(ts=ts, cmds=cmds, control_hub=control_hub, port=port)
			results = ["ERROR" not in j for j in [i["result"] for i in output]]
			if sum(results) == len(results):
		#		for thing in output:
		#			print "\t{0} -> {1}".format(thing["cmd"], thing["result"])
				return True
			else:
				print "ERROR (qie.set_ped): Setting pedestals resulted in the following:"
				for thing in output:
					print "\t{0} -> {1}".format(thing["cmd"], thing["result"])
				return False
		else:
			print "ERROR (qie.set_ped): The \"i_qie\" argument was not good."
			return False
	else:
		print "ERROR (qie.set_ped): The crate, slot arguments were not good."
		return False
## /

## Fixed Range Mode:
def set_fixed_range(ts=False, crate=None, slot=None, i_qie=None, enable=None, r=None, control_hub=None, port=ngfec.port_default):		# Turn fixed range mode on or off for a given QIE.
	# Parse "crate" and "slot":
	fe = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot)
	if fe:
		# Parse "i_qie":
		i_qie = meta.parse_args_qie(i_qie=i_qie)		# The default is range(1, 25)
		if i_qie:
			# Parse "r" and "enable":
			if enable == None:
				if r == None:
					r = 0
					enable = False
				else:
					if isinstance(r, int):
						r = int(r)
						if r in range(4):
							enable = True
						else:
							print "ERROR (qie.set_fixed_range): The range you select with \"r\" must be an element of [0, 1, 2, 3]."
							return False
					else:
						print "ERROR (qie.set_fixed_range): You need to make sure to input an integer value for \"r\"."
						return False
			else:
				enable = bool(enable)
			
			# Build list of commands:
			cmds = []
			for crate, slots in fe.iteritems():
				for slot in slots:
					for i in i_qie:
						if enable:
							cmds.extend([
								"put HF{0}-{1}-QIE{2}_FixRange 1".format(crate, slot, i),
								"put HF{0}-{1}-QIE{2}_RangeSet {3}".format(crate, slot, i, r),
								"get HF{0}-{1}-QIE{2}_FixRange".format(crate, slot, i),
								"get HF{0}-{1}-QIE{2}_RangeSet".format(crate, slot, i),
							])
						else :
							cmds.extend([
								"put HF{0}-{1}-QIE{2}_FixRange 0".format(crate, slot, i),
								"put HF{0}-{1}-QIE{2}_RangeSet 0".format(crate, slot, i),
								"get HF{0}-{1}-QIE{2}_FixRange".format(crate, slot, i),
								"get HF{0}-{1}-QIE{2}_RangeSet".format(crate, slot, i),
							])
			
			# Send commands:
			output = ngfec.send_commands(ts=ts, cmds=cmds, control_hub=control_hub, port=port)
			results = ["ERROR" not in j for j in [i["result"] for i in output]]
			if sum(results) == len(results):
#				for thing in output:
#					print "\t{0} -> {1}".format(thing["cmd"], thing["result"])
				return True
			else:
				print "ERROR (qie.set_fixed_range): Setting fixed-range mode resulted in the following:"
				for thing in output:
					print "\t{0} -> {1}".format(thing["cmd"], thing["result"])
				return False
		else:
			print "ERROR (qie.set_fixed_range): The \"i_qie\" argument was not good."
			return False
	else:
		print "ERROR (qie.set_fixed_range): The crate, slot arguments were not good."
		return False
## /

## Cal Mode:
def set_cal_mode(ts, crate, slot, qie, enable=False):
	value = 1 if enable else 0
	commands = ["put HF{0}-{1}-QIE{2}_CalMode {3}".format(crate, slot, qie, value)]
	raw_output = ngfec.send_commands(ts=ts, cmds=cmds)
	return raw_output

def set_cal_mode_all(ts, crate, slot, enable=False):
	commands = []
	value = 1 if enable else 0
	for qie in range(1, 25):
		commands.append("put HF{0}-{1}-QIE{2}_CalMode {3}".format(crate, slot, qie, value))
	raw_output = ngfec.send_commands(ts=ts, cmds=cmds)
	return raw_output
## /

## QIE clock phase:
def set_clk_phase(ts=False, crate=None, slot=None, i_qie=None, phase=0, control_hub=None, port=ngfec.port_default, script=True):
	# Parse "crate" and "slot":
	fe = meta.parse_args_crate_slot(ts=ts, crate=crate, slot=slot)
	if fe:
		# Parse "i_qie":
		i_qie = meta.parse_args_qie(i_qie=i_qie)		# The default is range(1, 25)
		if i_qie:
			# Parse "phase":
			if isinstance(phase, int):
				phase = int(phase)
				if phase not in range(16):
					print "ERROR (qie.set_clk_phase): The clock phase you selected with \"phase\" must be an element of [0, 1, ..., 15]."
					return False
			else:
				print "ERROR (qie.set_clk_phase): The clock phase you selected with \"phase\" must be an integer (between 0 and 15)."
				return False
			
			# Build list of commands:
			cmds = []
			for crate, slots in fe.iteritems():
				for slot in slots:
					for i in i_qie:
						cmds.extend([
							"put HF{0}-{1}-Qie{2}_ck_ph {3}".format(crate, slot, i, phase),
							"get HF{0}-{1}-Qie{2}_ck_ph".format(crate, slot, i),
						])
			
			# Send commands:
			output = ngfec.send_commands(ts=ts, cmds=cmds, control_hub=control_hub, port=port, script=script)
			results = ["ERROR" not in j for j in [i["result"] for i in output]]
			if sum(results) == len(results):
#				for thing in output:
#					print "\t{0} -> {1}".format(thing["cmd"], thing["result"])
				return True
			else:
				print "ERROR (qie.set_clk_phase): Setting QIE clock phase mode resulted in the following:"
				for thing in output:
					print "\t{0} -> {1}".format(thing["cmd"], thing["result"])
				return False
		else:
			print "ERROR (qie.set_clk_phase): The \"i_qie\" argument was not good."
			return False
	else:
		print "ERROR (qie.set_clk_phase): The crate, slot arguments were not good."
		return False
## /
# /

# Functions dealing with QIE chip behavior:
def make_adc_to_q_conversion():		# This function generates a list of charge values (in fC) indexed by ADC bin number.
	srs = [		# Subrange information
		range(0, 16),
		range(16, 36),
		range(36, 57),
		range(57, 64)
	]
	overlap = 3		# The number of bins that overlap at range transitions.
	s_init = 3.1		# All other ideal sensitivities can be calculated from this using s = s_init * (8**r) * (2**sr).
	s = 0
	s_sr_min = 0
#	p = -16
	p = 0
	q_sum = p
	q = []
	for r in range(4):
		for sr in range(4):
			for m in srs[sr]:
				s_prev = s
				s = s_init * (8**r) * (2**sr)		# Calculate the appropriate sensitivity.
				q_sum += s_prev/2 + s/2
				if sr == 0 and m == 0 and r > 0:
					q_sum -= s*overlap
				q.append(q_sum)
	return q
# /
# /FUNCTIONS


if __name__ == "__main__":
	print "Hang on."
	print 'What you just ran is "qie.py". This is a module, not a script. See the documentation ("readme.md") for more information.'
