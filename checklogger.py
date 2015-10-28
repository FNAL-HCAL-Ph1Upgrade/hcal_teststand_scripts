#!/usr/bin/python

# Small script to check whether the logger still works

# Will check whether files are still appearing, otherwise will send an email, and restart the logger

import smtplib		# For emailing.
from email.mime.text import MIMEText		# For emailing.
import datetime
from time import sleep
import os, glob, sys

def send_email(subject="", body=""):
	msg = MIMEText(body)
	msg['Subject'] = subject
	msg['From'] = "checklogger@teststand.hcal"
	msg['To'] = ""
	
	s = smtplib.SMTP_SSL('slmp-550-22.slc.westdc.net',465)
	s.login("alerts@connivance.net", "Megash4rk")
	s.sendmail(
		"alerts@connivance.net", 
		[
                        "pastika@fnal.gov",
			"nadja.strobbe@gmail.com"
		],
		msg.as_string()
	)
	s.quit()


def main():
    logdir = "/home/daq/nstrobbe/hcal_teststand_scripts/data/ts_HEcharm/"

    while True:

	    current_date = datetime.datetime.today()
	    current_date_s = current_date.strftime("%y%m%d")
	    current_datetime_s = current_date.strftime("%y%m%d_%H%M%S")

	    logdirs = sorted([_.split("/")[-1] for _ in glob.glob(logdir+"??????")])
	    # find last log
	    logs = sorted(glob.glob(logdir+"/"+logdirs[-1]+"/??????_??????.log"))
	    last_log_time = datetime.datetime.strptime(logs[-1].split("/")[-1].strip(".log"),"%y%m%d_%H%M%S")
	    tenmin = datetime.timedelta(minutes=20)
	    if not current_date - tenmin < last_log_time:
		    # Log didn't appear
		    send_email("Radiation test log files are not appearing",
			       "No log files have appeared since {0}.\nPlease get up and check the system. I have made an attempt to restart it, but you should check that there are no further issues...".format(last_log_time.strftime("%y%m%d_%H%M%S")))
		    print "Log didn't appear, trying to restart logger"
		    command = "nohup python /home/daq/nstrobbe/hcal_teststand_scripts/log_teststand.py -t 'HEfnal' -s 5 -f 30 &> /home/daq/nstrobbe/hcal_teststand_scripts/data/log_teststand_{0}.log &".format(current_datetime_s)
		    os.system(command)
	    else:
		    print "all ok"
		    
	    sleep(15*60)


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print "Too tired to continue..."
		sys.exit()
    
