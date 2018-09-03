#!/usr/bin/env python

import os, pexpect, re, sys
#import printer
from time import time

class ngfec:

    def __init__(self, host, port, logfile=sys.stdout):
        self.connect(host, port, logfile=logfile)

    def __del__(self):
        try:
            self.disconnect()
        except Exception:
            print "Failed to clean up ngFEC.exe client"

    def connect(self, host, port, logfile=sys.stdout):
        s = "ngFEC.exe -z -c -t -p %d -H %s" % (port, host)
        self.p = pexpect.spawn(s)
        self.p.logfile = logfile
        self.p.sendline("")
        self.p.expect(".*")
    
    
    def disconnect(self):
        self.p.sendline("quit")
        self.p.expect(pexpect.EOF)
        self.p.close()
    
    
    def survey_clients(self):
        os.system("ps -ef | grep %s | grep 'ngccm -z'" % os.environ["USER"])
    
    
    def kill_clients(self):
        os.system("killall ngccm >& /dev/null")
    
    
    def command(self, cmd, timeout=5, lastCmd=None):
        fields = cmd.split()
        if not fields:
            return None
    
        if fields[0] == "jtag":
            if len(fields) < 4:
                print("COMMAND has to few fields: (%s)" % cmd)
                return None
    
            regexp = "(.*)%s %s %s# retcode=(.*)" % tuple(fields[1:])
        else:
            if lastCmd:
                regexp = "{0}\s?#((\s|E)[^\r^\n]*)".format(re.escape(lastCmd))
            else:
                regexp = "{0}\s?#((\s|E)[^\r^\n]*)".format(re.escape(cmd))
    
        try:
            self.p.sendline(cmd)
            self.p.expect(regexp, timeout=timeout)
            #return self.p.match.group(0).split("\r\n")
            return self.p.match.group(1).strip().replace("'", "").replace("_rr", "")

        except pexpect.TIMEOUT:
            tail = ""#"tail -20 %s" % self.p.logfile.name
    
            msg  = 'The command "'
            msg += cmd
            msg += '"\n       produced unexpected output.  Consult the log file, e.g.'
            msg += '\n       "%s" gives this:' % tail
            print msg


    def send_commands(self, cmds, timeout=10, script = False):
        if script:
            with file("ngfec_script", "w") as fout:
                fout.write("\n".join(cmds))
                fout.write("\n")

            output = []
                                
            try:
                self.p.sendline("< ngfec_script")   
                #results = self.command("<ngfec_script", timeout + 0.5*len(cmds), lastCmd=cmds[-1])
                for i, c in enumerate(cmds):
                    # Deterimine how long to wait until the first result is expected:
                
                    # parse commands:
                    t0 = time()
                    self.p.expect("{0}\s?#((\s|E)[^\r^\n]*)".format(re.escape(c)), timeout=timeout)
                    t1 = time()
                
                    try:
                        output.append({
                            "cmd": c.replace("_rr", ""),
                            "result": self.p.match.group(1).strip().replace("'", "").replace("_rr", "").split('#')[0],
                            "times": [t0, t1],
                        })
                    except AttributeError:
                        print "Command failed: ", c
            except pexpect.TIMEOUT:
                tail = ""#"tail -20 %s" % self.p.logfile.name
    
                msg  = 'The command "'
                msg += '"\n       produced unexpected output.  Consult the log file, e.g.'
                msg += '\n       "%s" gives this:' % tail
                print msg
                print cmds


            #output.append({
            #    "cmd": c.replace("_rr", ""),
            #    "result": self.p.match.group(1).strip().replace("'", "").replace("_rr", "").split('#')[0],
            #    "times": [t0, t1],
            #})

            return output
        else:
            output = []
            for cmd in cmds:
                t0 = time()
                result = self.command(cmd, timeout)
                t1 = time()
                try:
                    output.append({'cmd':cmd.replace("_rr", ""), 'result':result.split('#')[0], "times":[t0, t1]})
                except AttributeError:
                    print "Command failed: ", cmd
            return output
