####################################################################
# Type: MODULE                                                     #
#                                                                  #
# Description: The ngFEC                                           #
####################################################################

# IMPORTS:
from re import search, escape
import pexpect
from time import time, sleep
## hcal_teststand_scripts imports:
import meta
# /IMPORTS

# VARIABLES:
cmds_default = ["quit"]
port_default = 4242
# /VARIABLES

# CLASSES:
# /CLASSES

# FUNCTIONS:
def send_commands(ts=None, control_hub=None, port=port_default, cmds=cmds_default, script=False, raw=False):
	# Arguments and variables
	output = []
	raw_output = ""
	## Parse ngFEC server port:
	port = meta.parse_args_port(ts=ts, port=port)		# Uses "ts.ngfec_port" unless a ts is not specified.
	## Parse control_hub argument:
	control_hub = meta.parse_args_hub(ts=ts, control_hub=control_hub)		# Uses "ts.control_hub" unless a ts is not specified.
	if control_hub != False and port:		# Potential bug if "port=0" ... (Control_hub should be allowed to be None.)
		## Parse commands:
		if isinstance(cmds, str):
			cmds = [cmds]
		if not script:
			if "quit" not in cmds:
				cmds.append("quit")
		else:
			cmds = [c for c in cmds if c != "quit"]		# "quit" can't be in a ngFEC script.
			cmds_str = ""
			for c in cmds:
				cmds_str += "{0}\n".format(c)
			file_script = "ngfec_script"
			with open(file_script, "w") as out:
				out.write(cmds_str)
		
		# Prepare the ngfec arguments:
		ngfec_cmd = 'ngFEC.exe -z -c -p {0}'.format(port)
		if control_hub != None:
			ngfec_cmd += " -H {0}".format(control_hub)
		
		# Send the ngfec commands:
#		print ngfec_cmd
		p = pexpect.spawn(ngfec_cmd)
#		print p.pid
		if not script:
			for i, c in enumerate(cmds):
#				print c
				p.sendline(c)
				if c != "quit":
					t0 = time()
					p.expect("{0}\s?#((\s|E)[^\r^\n]*)".format(escape(c)))
					t1 = time()
#					print [p.match.group(0)]
					output.append({
						"cmd": c,
						"result": p.match.group(1).strip().replace("'", ""),
						"times": [t0, t1],
					})
					raw_output += p.before + p.after
		else:
			p.sendline("< {0}".format(file_script))
			for i, c in enumerate(cmds):
				# Deterimine how long to wait until the first result is expected:
				if i == 0:
					timeout = max([30, int(0.0075*len(cmds))])
#					print i, c, timeout
				else:
					timeout = 30		# pexpect default
#					print i, c, timeout
#				print i, c, timeout
				
				# Send commands:
				t0 = time()
				p.expect("{0}\s?#((\s|E)[^\r^\n]*)".format(escape(c)), timeout=timeout)
				t1 = time()
#				print [p.match.group(0)]
				output.append({
					"cmd": c,
					"result": p.match.group(1).strip().replace("'", ""),
					"times": [t0, t1],
				})
				raw_output += p.before + p.after
			p.sendline("quit")
		p.expect(pexpect.EOF)
		raw_output += p.before
#		sleep(1)		# I need to make sure the ngccm process is killed.
		p.close()
#		print "closed"
		killall()
		if raw:
			return raw_output
		else:
			return output

def killall():
	p = pexpect.spawn('killall ngccm')		# Run script.
	p.expect(pexpect.EOF)		# Wait for the script to finish.
	raw_output = p.before.strip()		# Collect all of the script's output.
	return raw_output
# /FUNCTIONS
