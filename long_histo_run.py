import hcal_teststand.uhtr as uhtr
import hcal_teststand.hcal_teststand as hc
from hcal_teststand.utilities import time_string
from time import sleep
import sys

def main(ts):
    t = time_string()[:-4]
    histo_output = uhtr.get_histos(ts,
                                   n_orbits=10000,
                                   sepCapID=0,
                                   file_out_base="{0}/histo_{1}".format("data/long_histos/CuTest", t),
                                   script = False)                                           


if __name__ == "__main__":
    try:

        ts = hc.teststand("HEcharm")

        #while True:
        for i in range(60):
            #print "Starting histo run at", time_string()[:-4]
            main(ts)
            #print "Finished histo run at", time_string()[:-4]
            #sleep(60*30)

    except KeyboardInterrupt:
        print "Bye!"
        sys.exit()
