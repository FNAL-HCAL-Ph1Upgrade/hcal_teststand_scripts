import pexpect
from utilities import time_string
from time import time

def get_power(ts, num=6):
	try:
		p = pexpect.spawn('/home/daq/gpib/kam/lowVoltage {0}'.format(num))
		# Run script.
		p.expect(pexpect.EOF)		# Wait for the script to finish.
		raw_output = p.before.strip()		# Collect all of the script's output.
		results = [float(value[:-1]) for value in raw_output.split()]
	except Exception as ex:
		print ex
		results = [-1, -1]
	return {
		"V": results[0],
		"I": results[1],
#		"time": time_string(),
		"time": time(),
	}

def enable_power(enable=0):
	try:
		p = pexpect.spawn('/home/daq/gpib/kam/backup/lowVoltage_output {0}'.format(enable))		# Run script.
		p.expect(pexpect.EOF)		# Wait for the script to finish.
		raw_output = p.before.strip()		# Collect all of the script's output.
	except Exception as ex:
		print ex
		raw_output = str(ex)
	return raw_output

def config_power():
	try:
		p = pexpect.spawn('/home/daq/gpib/kam/backup/lowVoltage_config')		# Run script.
		p.expect(pexpect.EOF)		# Wait for the script to finish.
		raw_output = p.before.strip()		# Collect all of the script's output.
	except Exception as ex:
		print ex
		raw_output = str(ex)
	return raw_output
