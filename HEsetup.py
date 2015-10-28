import log_teststand
import hcal_teststand.hcal_teststand as hc
import os
from optparse import OptionParser
import hcal_teststand.uhtr as uhtr


parser = OptionParser()
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

(options, args) = parser.parse_args()

reset = False
setup = False
link = False
if options.all:
    reset = True
    setup = True
    link = True

if options.reset:
    reset = True
if options.setup:
    setup = True
if options.link:
    link = True

if reset:
    # Do a reset
    os.system("source /home/daq/pastika/reset.sh")

ts = hc.teststand("HEcharm")

if link:
    # initialize the links
    uhtr.initLinks(ts, OrbitDelay=33, Auto_Realign=1, OnTheFlyAlignment=0, CDRreset=0, GTXreset=0, verbose=True)
    print uhtr.linkStatus(ts)

if setup:
    log_teststand.HEsetup(ts)

