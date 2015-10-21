####################################################################
# Type: MODULE                                                     #
#                                                                  #
# Description: [description]                                       #
####################################################################

# IMPORTS:
import sys
import os
from optparse import OptionParser
from ..hcal_teststand import teststand
from ..utilities import time_string, logger
from ..mapping import *
from ..qie import get_unique_id
#import ROOT
# /IMPORTS

# VARIABLES:
#ts = teststand("904at")
# /VARIABLES

# CLASSES:
class acceptance:
	# Construction:
	def __init__(self, name=None):
		# Assign argument variables:
		if name:
			self.name = name
			if (self.name.split("_")[0] == "at"):		# Remove a preceding "at_" if there is one.
				self.name = self.name[3:]
		else:
			print "ERROR (tests.acceptance.__init__): You need to initialize an acceptance test with the three character name (like \"reg\")."
			self.exit()
		
		# Assign commandline option variables:
		## Define commandline options:
		### Teststand:
		parser = OptionParser()
		parser.add_option("-t", "--teststand", dest="ts",
			default="904at",
			help="The name of the teststand you want to use (default is \"904at\")",
			metavar="STR"
		)
		### QIE Info:
#		parser.add_option("-q", "--qid", dest="qid",
#			default="0x67000000 0x9b32c370",
#			help="The unique ID of the QIE card you're testing (default is \"0x67000000 0x9b32c370\")",
#			metavar="STR"
#		)
		parser.add_option("-c", "--fecrate", dest="c",
			default=2,
			help="FE crate (default is 2)",
			metavar="INT"
		)
		parser.add_option("-s", "--feslot", dest="s",
			default=2,
			help="FE slot (default is 2)",
			metavar="INT"
		)
		parser.add_option("-C", "--becrate", dest="C",
			default=53,
			help="BE crate (default is 53)",
			metavar="INT"
		)
		parser.add_option("-S", "--beslot", dest="S",
			default=1,
			help="BE slot (default is 1)",
			metavar="INT"
		)
		parser.add_option("-l", "--link", dest="l",
			default=12,
			help="Starting link number (default is 18).",
			metavar="INT"
		)
		### Verbose mode:
		parser.add_option("-v", "--verbose", dest="v",
			action="store_true",
			default=False,
			help="Turn on verbose mode (default is off)",
			metavar="BOOL"
		)
		### N values:
		parser.add_option("-n", "--n", dest="n",
			default=10,
			help="An n value for this test. It is used in different ways depending on the test. (Defualt is 10.)",
			metavar="INT"
		)
		(options, args) = parser.parse_args()
		
		## Assign variables:
		self.ts_name = options.ts
		self.fe_crate = int(options.c)
		self.fe_slot = int(options.s)
		self.be_crate = int(options.C)
		self.be_slot = int(options.S)
		self.i_link = int(options.l)
#		self.qid = options.qid
		self.verbose = self.v = int(options.v)
		self.n = int(options.n)
		
		# Other variables:
		## Unique ID:
		qid_result = get_unique_id(crate=self.fe_crate, slot=self.fe_slot, control_hub="hcal904daq01")
		qid_list = qid_result[self.fe_crate, self.fe_slot]
		if qid_list:
			self.qid = qid_list[0] + " " + qid_list[1]
#			print self.qid
		else:
			print "ERROR (test.acceptance.__init__): Could not read the unique ID from the card in FE Crate {0}, Slot {1}:".format(self.fe_crate, self.fe_slot)
			print qid_result
			self.exit()
		
		## Output location:
		self.time_string = time_string()[:-4]
		self.path = "/nfshome0/elhughes/public/data/at_results/{0}/at_{1}/{2}".format(self.qid.replace(" ", "_"), self.name, self.time_string)
		if not os.path.exists(self.path):
			os.makedirs(self.path)		# Sometimes the "umask" prevents setting the permissions here, so I do it on the next line.
			os.chmod(self.path, 0777)
		self.file_name = "{0}_{1}".format(self.time_string, self.name)
		sys.stdout = logger(f="{0}/{1}.txt".format(self.path, self.file_name))
		
		## Mapping:
		self.chart = chart(name=self.ts_name)
		self.chart.add_map(mapping.single_card(
			qid=self.qid,
			fe_crate=self.fe_crate,
			fe_slot=self.fe_slot,
			be_crate=self.be_crate,
			be_slot=self.be_slot,
			link=self.i_link,
		))
		self.chart.write()
		
		## Teststand objects:
		self.ts = teststand(self.ts_name, fe_crate=self.fe_crate, fe_slot=self.fe_slot, be_crate=self.be_crate, be_slot=self.be_slot)
#		print self.ts.uhtrs
		self.qie = self.ts.qies.values()[0]
		self.uhtr = self.ts.uhtrs.values()[0]
		self.ngccm = self.ts.ngccms.values()[0]
		self.be_crate = self.uhtr.be_crate
		self.be_slot = self.uhtr.be_slot
		self.fe_crate = self.qie.fe_crate
		self.fe_slot = self.qie.fe_slot
		self.links = self.uhtr.links[self.be_crate, self.be_slot]
		
		# ROOT setup:
		ROOT.gROOT.SetStyle("Plain")
		ROOT.gStyle.SetTitleBorderSize(0)
		ROOT.gStyle.SetPalette(1)
		ROOT.gROOT.SetBatch()
		
		## ROOT output:
		self.out = ROOT.TFile("{0}/{1}.root".format(self.path, self.file_name), "RECREATE")
		ROOT.SetOwnership(self.out, 0)
		self.canvas = ROOT.TCanvas("c0", "c0", 500, 500)
		self.canvas.SetFillColor(ROOT.kWhite)
		ROOT.SetOwnership(self.canvas, 0)
	# /Construction
	
	# Methods:
	def exit(self):
		print "[!!] Acceptance test aborted."
		sys.exit()
	
	def log(self, s="[empty line]"):
		sys.stdout.log.write("{0}\n".format(s))
		return s
	
	def start(self, update=True):
		print "\nRunning the {0} acceptance test ...".format(self.name)
		print "\tQIE card: ID = {0} (FE Crate {1}, Slot {2})".format(self.qid, self.fe_crate, self.fe_slot)
		print "\tuHTR: Links = {0} (BE Crate {1}, Slot {2})".format([l.n for l in self.links], self.be_crate, self.be_slot)
#		print self.qie.check_unique_id()
		if update:
			print "Fetching FW version information ..."
			result = self.ts.update()
			if result:
				print "\t[OK] QIE card: FW = {0}".format(self.qie.fws)
				print "\t[OK] uHTR: FW = {0}".format(self.uhtr.fws)
				print "\t[OK] ngCCM: FW = {0}, ID = {1}".format(self.ngccm.fw, " ".join(self.ngccm.id))
				print "Checking the unique ID ..."
				if self.qie.check_unique_id():
					print "\t[OK]"
					return True
				else:
					print "[!!] ERROR (tests.acceptance.start): Failed to write the unique ID to the IGLOO2s."
#					return False
					self.exit()
			else:
				print "[!!] ERROR (tests.acceptance.start): Failed to updated the teststand object."
#				return False
				self.exit()
		else:
			print "Skipping fetching FW version information ..."
			return True
	
	def write(self):
		print "Saving output to {0} ...".format(self.path)
#		tc = self.canvas.Clone()
		self.canvas.SaveAs("{0}/{1}.pdf".format(self.path, self.file_name))
		self.canvas.SaveAs("{0}/{1}.png".format(self.path, self.file_name))		# This can cause a crash on divided canvases for some reason.
		self.out.Close()
		print "\t[OK]"
	# /Methods
# /CLASSES

# FUNCTIONS:
# /FUNCTIONS
