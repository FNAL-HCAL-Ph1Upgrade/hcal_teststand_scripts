import hcal_teststand.uhtr as uhtr
import hcal_teststand.hcal_teststand as hc
from hcal_teststand.utilities import time_string
from time import sleep
import sys

def main():
    t = time_string()[:-4]

    ts = hc.teststand("HEcharm")

    histo_output = uhtr.get_histos(ts,
                                   n_orbits=10000000,
                                   sepCapID=0,
                                   file_out_base="{0}/histo_{1}".format("data/long_histos", t),
                                   script = False)                                           


if __name__ == "__main__":
    try:

        while True:
            print "Starting histo run at", time_string()[:-4]
            main()
            print "Finished histo run at", time_string()[:-4]
            sleep(60*30)

    except KeyboardInterrupt:
        print "Bye!"
        sys.exit()
