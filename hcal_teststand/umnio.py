####################################################################
# Type: MODULE                                                     #
#                                                                  #
# Description: This module contains functions for talking to the   #
# uHTRs.                                                           #
####################################################################
#
from re import search
from subprocess import Popen, PIPE
import hcal_teststand
import meta
from time import sleep
import os

# VARIABLES:
cmds_default = ["0", "exit", "exit"]
# /VARIABLES

# CLASSES:
class umnio:
        # Construction:
        def __init__(self, ts=None, crate=None, slot=None, ip=None):
                self.ts = ts
                self.end = "be"
                self.be_crate = self.crate = crate
                self.be_slot = self.slot = slot
                self.ip = ip
                if hasattr(ts, "control_hub"):
                        self.control_hub = ts.control_hub
        
        # String behavior
        def __str__(self):
                try:
                        return "<uMNio in BE Crate {0}, BE Slot {1}: IP = {2}>".format(self.crate, self.slot, self.ip)
                except Exception as ex:
                        return "<empty umnio object>"
        
        # Methods:        
        def Print(self):
                print self
        
        def send_commands(self, cmds=cmds_default, script=False):
                return send_commands(control_hub=self.control_hub, ip=self.ip, cmds=cmds, script=script)
        
# /CLASSES

# FUNCTIONS:
def send_commands(ts=None, crate=None, slot=None, ip=None, control_hub=None, cmds=cmds_default, script=False):
        # Sends commands to "uHTRtool.exe" and returns the raw output and a log. The input is a teststand object and a list of commands.
        # Arguments and variables:
        raw = ""
        results = {}                # Results will be indexed by uHTR IP unless a "ts" has been specified, in which case they'll be indexed by (crate, slot).
        
        ## Parse ip argument:
        ips = meta.parse_args_ip(ts=ts, crate=crate, slot=slot, ip=ip)
        if ips:
                ## Parse control_hub argument:
                control_hub = meta.parse_args_hub(ts=ts, control_hub=control_hub)
        
                ## Parse cmds:
                if isinstance(cmds, str):
                        print 'WARNING (umnio.send_commands): You probably didn\'t intend to run "uMNioTool.exe" with only one command: {0}'.format(cmds)
                        cmds = [cmds]
                cmds_str = ""
                for c in cmds:
                        cmds_str += "{0}\n".format(c)

                # Send the commands:
                for uhtr_ip, crate_slot in ips.iteritems():
                        # Prepare the uHTRtool arguments:
                        uhtr_cmd = "uMNioTool.exe {0}".format(uhtr_ip)
                        if control_hub:
                                uhtr_cmd += " -o {0}".format(control_hub)
                        # Send commands and organize results:
                        if script:
                                with open("umnio_script.cmd", "w") as out:
                                        out.write(cmds_str)
#                                print uhtr_cmd
                                raw_output = Popen(['{0} < umnio_script.cmd'.format(uhtr_cmd)], shell = True, stdout = PIPE, stderr = PIPE).communicate()
                        else:
                                raw_output = Popen(['printf "{0}" | {1}'.format(cmds_str, uhtr_cmd)], shell = True, stdout = PIPE, stderr = PIPE).communicate()                # This puts the output of the command into a list called "raw_output" the first element of the list is stdout, the second is stderr.
                        raw += raw_output[0] + raw_output[1]
                        if crate_slot:
                                results[crate_slot] = raw
                        else:
                                results[uhtr_ip] = raw
                return results
        else:
                return False



def getDTCstatus(ip=None, cmds=cmds_default, script=False):
        """
        Get the DTC status for this uMNio.
        """

        cmds = [
                '0',
		'DTC',
		'status',
		'quit',
                'exit',
                'exit',
                ]
        
        result = send_commands(ip=ip, cmds=cmds, script=script)

        if result:
		info = result[ip].split("================================================")[-1].split("\n")[1:13]
                return "\n".join(info)
        else:
                return False


if __name__ == "__main__":
        print "Hang on."
        print 'What you just ran is "umnio.py". This is a module, not a script. See the documentation ("readme.md") for more information.'
