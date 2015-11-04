import iglooSpyHE as ispy
from optparse import OptionParser

if __name__ == "__main__":
    

    parser = OptionParser()
    parser.add_option("-l", dest="long",
                      default=None, type="string",
                      metavar="SPY",
                      help="Convert full output into adc, tdc and capid info. %metavar should be of the the form X 0xYYYYYYYY 0xYYYYYYYY 0xYYYYYYYY 0xYYYYYYYY 0xYYYYYYYY 0xYYYYYYYY ")
    parser.add_option("-s", dest="short",
                      default=None, type="string",
                      metavar="QIEinfo",
                      help="Convert info on one qie into adc, tdc and capid. %metavar should be of the form 0xYYYY.")

    (options, args) = parser.parse_args()


    if options.long != None:
        parsed_info = ispy.getInfoFromSpy([options.long])
        print "Parsing {0}".format(options.long)
        for parsed in parsed_info[0]:
            print parsed

    if options.short != None:
        parsed = ispy.getInfoFromSpy_per_QIE(options.short)
        print "{0} -> {1}".format(options.short,parsed)
