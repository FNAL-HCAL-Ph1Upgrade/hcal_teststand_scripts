## Put a class here to hold the expected values for the links and registers
## Also keep track of registers that are expected to change


class LinkParameters:
    """A class to hold input information for the links."""

    def __init__(self, tstype="HEfnal"):
        self.Auto_Realign = 1
        self.OnTheFlyAlignment = 0
        self.CDRreset = 0
        self.GTXreset = 1
        if tstype == "HEfnal":
            self.OrbitDelay = 44
        else:
            # Not implemented yet
            self.OrbitDelay = 50


class QIERegisters:
    """A class to hold the expected QIE registers, 
and to store the current state of the ones we expect to change."""

    def __init__(self, tstype="HEfnal"):
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
        self.CkOutEn = 0
        self.Gsel = 0
        self.PedestalDAC = 0x26 
        self.TGain = 0
        self.Trim = 2


class IglooRegisters:
    """ A class to hold the expected igloo registers, 
and to store the current state of the ones we expect to change."""
    
    def __init__(self, tstype="HEfnal"):
        self.FPGA_MINOR_VERSION = 5 
        self.FPGA_MAJOR_VERSION = 0
        self.ZerosRegister = 0
        self.OnesRegister = 0xffffffff
        self.FPGA_TopOrBottom = 0
        self.StatusReg_InputSpyFifoEmpty = 1
        self.StatusReg_InputSpyFifoFull = 0
        self.StatusReg_InputSpyWordNum = 0
        self.StatusReg_PLL320MHzLock = 1
        self.StatusReg_BRIDGE_SPARE = 0
        self.StatusReg_QieDLLNoLock = 0
        self.StatusReg_zero = 0
        self.WTE_count = 0
        self.Clk_count = 0
        self.RST_QIE_count = 0
        self.CapIdErrLink1_count = 0 # If not we need to check if it increased, or maybe do a reset?
        self.CapIdErrLink2_count = 0
        self.CapIdErrLink3_count = 0
        self.CntrReg_WrEn_InputSpy = 0
        self.CntrReg_OrbHistoRun = 0
        self.CntrReg_CImode = 0
        self.CntrReg_InternalQIER = 0
        self.CntrReg_OrbHistoClear = 0
        
        nqies = 48
        for _ in range(nqies):
            setattr(self, 'Qie{0}_ck_ph'.format(_), 0) 

    def update_WTE_count(self, new_value):
        self.WTE_count = new_value

    def update_Clk_count(self, new_value):
        self.Clk_count = new_value

    def update_RST_QIE_count(self, new_value):
        self.RST_QIE_count = new_value


class BridgeRegisters:
    """A class to hold the expected bridge registers, 
and to store the current state of the ones we expect to change."""

    def __init__(self):
        pass


class ControlCardRegisters:
    """A class to hold the information from the SiPM control card. """

    def __init__(self):
        pass




class TestStandStatus:
    """A class to hold the expected state of the system, 
along with the current state of registers 
that are expected to change"""

    def __init__(self, tstype="HEfnal"):
        self.consts = {"Links":LinkParameters(tstype)}
        self.transients = {}
