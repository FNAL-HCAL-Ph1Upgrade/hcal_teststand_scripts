import log_teststand
import hcal_teststand.hcal_teststand as hc
import os, sys
from optparse import OptionParser
import hcal_teststand.uhtr as uhtr


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
    log_teststand.HEtogglebkp_pwr(ts)

if reset:
    log_teststand.HEreset(ts)

if link and tstype != "HEoven":
    # initialize the links
    uhtr.initLinks(ts, OrbitDelay=53, Auto_Realign=1, OnTheFlyAlignment=0, CDRreset=1, GTXreset=1, verbose=True)
    print uhtr.linkStatus(ts)

if setup:
    log_teststand.HEsetup(ts)

