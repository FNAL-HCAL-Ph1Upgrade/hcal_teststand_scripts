## Put a class here to hold the expected values for the links and registers
## Also keep track of registers that are expected to change

import hcal_teststand.hcal_teststand as hc

class LinkParameters:
    """A class to hold input information for the links."""

    def __init__(self, tstype="HEfnal"):
        """Initialize the Link parameters. 
OrbitDelay is put to 50, except for teststand HEfnal for which it is 44"""
        self.Auto_Realign = 1
        self.OnTheFlyAlignment = 0
        self.CDRreset = 1
        self.GTXreset = 1
        self.OrbitDelay = 53
        self.n_active_links = 10
        self.maxADC = 100
        self.maxAveADC = 20            

class ControlRegisters:
    def __init__(self, tstype="HEcharm"):
        self.fec_rx_prbs_error_cnt = 0
        self.fec_rx_rs_err_cnt = 0
        self.mezz_rx_prbs_error_cnt = 0
        self.b2b_rx_prbs_error_cnt = 0
        self.sb2b_rx_prbs_error_cnt = 0
        self.SinErr_cnt = 0
        self.DbErr_cnt = 0
        self.fec_dv_down_cnt = 0
        
class ControlLink:
    def __init__(self):
        self.qie_reset_early_cnt = 0
        self.qie_reset_late_cnt = 0
        self.mezz_scratch = '0xf 0xf 0xf 0xf'
    
class QIERegisters:
    """A class to hold the expected QIE registers, and to store the current state of the ones we expect to change."""

    def __init__(self, tstype="HEfnal"):
        """Initialize the QIERegisters object. For now it assumes that these are QIE11s"""
        self.CapID0pedestal = 0
        self.CapID1pedestal = 0
        self.CapID2pedestal = 0
        self.CapID3pedestal = 0
        self.DiscOn = 0
        self.Idcset = 0
        self.RangeSet = 0
        self.TimingIref = 0
        self.ChargeInjectDAC = 0
        self.FixRange = 0
        self.Lvds = 1
        self.TDCmode = 0
        self.TimingThresholdDAC = 0xff
        self.CkOutEn = 1
        self.Gsel = 0
        self.PedestalDAC = 0x26 
        self.TGain = 0
        self.Trim = 2


class IglooRegisters:
    """ A class to hold the expected igloo registers, and to store the current state of the ones we expect to change."""
    
    def __init__(self, qiecard, qies_per_card, tstype):
        """Initialize the igloo registers."""
        # These are the fixed ones
        self.FPGA_MINOR_VERSION = 0xb 
        #if tstype == "HEfnal":
        #    self.FPGA_MINOR_VERSION = 5
        self.FPGA_MAJOR_VERSION = 0
        self.ZerosRegister = 0
        self.OnesRegister = 0xffffffff
        self.FPGA_TopOrBottom = 0
        #self.StatusReg_InputSpyFifoEmpty = 1
        #self.StatusReg_InputSpyFifoFull = 0
        #self.StatusReg_InputSpyWordNum = 0
        self.StatusReg_PLL320MHzLock = 1
        self.StatusReg_BRIDGE_SPARE = 0
        self.StatusReg_QieDLLNoLock = 0
        self.StatusReg_zero = 0
        #self.CntrReg_WrEn_InputSpy = 0
        self.CntrReg_OrbHistoRun = 0
        self.CntrReg_CImode = 0
        self.CntrReg_InternalQIER = 0
        self.CntrReg_OrbHistoClear = 0
        self.CapIdErrLink3_count = 0
        self.scratch = 0xab

        for j in xrange(qies_per_card):
            setattr(self, 'Qie{0}_ck_ph'.format((qiecard-1)*qies_per_card+j+1), 0) 

        # These should be increasing
        self.WTE_count = 0
        self.Clk_count = 0
        self.RST_QIE_count = 0

        # These can go up, not necessarily because of radiation, but could be
        # So we should keep track of it
        self.CapIdErrLink1_count = 0 
        self.CapIdErrLink2_count = 0
        
    def update_WTE_count(self, new_value):
        self.WTE_count = new_value

    def update_Clk_count(self, new_value):
        self.Clk_count = new_value

    def update_RST_QIE_count(self, new_value):
        self.RST_QIE_count = new_value

    def update_CapIdErrLink1_count(self, new_value):
        self.CapIdErrLink1_count = new_value

    def update_CapIdErrLink2_count(self, new_value):
        self.CapIdErrLink2_count = new_value

    def update_transients(self, new_values):
        """Update all transient variables: WTE_count, Clk_count, RST_QIE_count, CapIdErrLink1_count and CapIdErrLink2_count. Expects a dictionary as input with format {'variable name':new_value}"""
        self.update_WTE_count(new_values["WTE_count"])
        self.update_Clk_count(new_values["Clk_count"])
        self.update_RST_QIE_count(new_values["RST_QIE_count"])
        self.update_CapIdErrLink1_count(new_values["CapIdErrLink1_count"])
        self.update_CapIdErrLink2_count(new_values["CapIdErrLink2_count"])
        
        
class BridgeRegisters:
    """A class to hold the expected bridge registers, 
and to store the current state of the ones we expect to change."""

    def __init__(self, tstype="HEfnal"):
        """Initialize the bridge registers."""
        # fixed ones
        self.FIRMVERSION_MAJOR = 1
        self.FIRMVERSION_MINOR = 0xe
        self.FIRMVERSION_SVN = 0x1140
        self.ZEROES = 0
        self.ONES = 0xffffffff
        self.ONESZEROES = 0xaaaaaaaa
        self.SCRATCH = 0xab

        # These should be increasing
        self.WTECOUNTER = 0
        self.CLOCKCOUNTER = 0
        self.RESQIECOUNTER = 0

        # Not sure if this needs to be monitored
        #self.SHT_temp_f

    def update_WTECOUNTER(self, new_value):
        self.WTECOUNTER = new_value

    def update_CLOCKCOUNTER(self, new_value):
        self.CLOCKCOUNTER = new_value

    def update_RESQIECOUNTER(self, new_value):
        self.RESQIECOUNTER = new_value

    def update_transients(self, new_values):
        """Update all transient variables: WTECOUNTER, CLOCKCOUNTER, RESQIECOUNTER. Expects a dictionary as input with format {'variable name':new_value}"""
        self.update_WTECOUNTER(new_values["WTECOUNTER"])
        self.update_CLKCOUNTER(new_values["CLOCKCOUNTER"])
        self.update_RESQIECOUNTER(new_values["RESQIECOUNTER"])


class ControlCardRegisters:
    """A class to hold the information from the SiPM control card. """

    def __init__(self, tstype):
        self.peltier_adjustment_f = 0.25
        self.peltier_control = 1
        self.peltier_stepseconds = 0x384
        self.peltier_targettemperature_f = 20.0
        #self.PeltierVoltage_f = 
        #self.PeltierCurrent_f = 
        #self.BVin_f = 
        #self.Vin_f = 
        #self.Vt_f =
        #self.Vdd_f =
        #if tstype == "HEcharm":
            #for i in [1,15,39]:
                #setattr(self, "biasmon{0}_f".format(i), 69.0)
                #setattr(self, "LeakageCurrent{0}_f".format(i), )



class TestStandStatus:
    """A class to hold the expected state of the system, 
along with the current state of registers 
that are expected to change"""

    def __init__(self, ts):

        # Check whether a teststand status was provided
#        if not isinstance(ts, hc.teststand):
#            raise TypeError("You should create the TestStandStatus object with a teststand object!!")

        self.tstype = ts.name
        
        # Store the links, for now one object, so assumes same orbitdelay
        self.links = LinkParameters(self.tstype)

        # Store the control registers
        self.control = {}
        for crate in ts.fe_crates:
            self.control[crate] = ControlRegisters(self.tstype)

        self.controllinks = {}
        for crate in ts.fe_crates:
            self.controllinks[crate] = ControlLink()

        # Store the QIE information, put them in a list per crate, slot combo
        self.qies = {}
        for icrate, crate in enumerate(ts.fe_crates):
            for qie in xrange(ts.qies_per_card):
                self.qies[crate,"calib",qie+1] = QIERegisters(self.tstype)
            for slot in ts.qie_slots[icrate]:
                for qiecard in ts.qiecards[crate][slot]:
                    for qie in xrange(ts.qies_per_card):
                        self.qies[crate, slot, (qiecard-1)*ts.qies_per_card+qie+1] = QIERegisters(self.tstype)

        # Store the igloo information
        self.igloos = {}
        for icrate, crate in enumerate(ts.fe_crates):
            self.igloos[crate, "calib", 1] = IglooRegisters(1, ts.qies_per_card, self.tstype)

            for slot in ts.qie_slots[icrate]:
                for qiecard in ts.qiecards[crate][slot]:
                    self.igloos[crate, slot, qiecard] = IglooRegisters(qiecard, ts.qies_per_card, self.tstype)

        # Store the bridge information
        self.bridges = {}
        for icrate, crate in enumerate(ts.fe_crates):
            self.bridges[crate, "calib", 1] = BridgeRegisters(self.tstype)
            for slot in ts.qie_slots[icrate]:
                for qiecard in ts.qiecards[crate][slot]:
                    self.bridges[crate, slot, qiecard] = BridgeRegisters(self.tstype)

        # Store the control card information
        self.controlcards = {}
        for icrate, crate in enumerate(ts.fe_crates):
            for slot in ts.qie_slots[icrate]:
                self.controlcards[crate,slot] = ControlCardRegisters(self.tstype)

        
