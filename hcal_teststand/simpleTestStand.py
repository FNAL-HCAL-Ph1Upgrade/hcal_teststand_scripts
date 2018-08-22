from ngfec_ted import ngfec

class UHTR:
    def __init__(self, crate = 41, slot = 5):
        self.crate = crate
        self.slot = slot
        self.ip = "192.168.%i.%i"%(crate, slot*4)

class teststand:
    def __init__(self):
        self.name = "bob"
        self.port = 64000
        self.ngfec_port = self.port
        self.control_hub = "localhost"
        self.fe_crates = ["HB1",]
        self.qie_slots = [[1,2]]
        self.qiecards = {"HB1":{1:[1,2,3,4,],2:[1,2,3,4]}}
        self.qies_per_card = 16
        self.uhtrs = {("HB1",1):UHTR(41, 5),}
        self.ngfec = ngfec(self.control_hub, self.port, None)
        self.be = None

    def uhtr_ip(self, crate, slot):
        return "192.168.%i.%i"%(crate, slot*4)


