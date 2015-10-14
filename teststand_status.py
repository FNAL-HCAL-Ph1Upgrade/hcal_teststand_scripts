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

class TestStandStatus:
    """A class to hold the expected state of the system, 
along with the current state of registers 
that are expected to change"""

    def __init__(self, tstype="HEfnal"):
        self.consts = {"Links":LinkParameters(tstype)}
        self.transients = {}
