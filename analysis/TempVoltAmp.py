import matplotlib.dates as mdates
import pandas as pd
import time
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
i = 0
#df = pd.DataFrame(columns=['Time','Volts','Amps','C'])
f = open("TempVoltAmp_Log.txt")
lines = f.readlines()
data = []
lastut = 0
for line in lines:
	log = {}
	i+=1
	if i%6 == 2:
                try:
                        dt = datetime.strptime(line, '%Y-%m-%d %H:%M:%S.%f ')
                        ut = time.mktime(dt.timetuple())
                        if ut - lastut > 11:
                                print "Power cycle at: ", line
                        lastut = ut
                except ValueError:
                        i = 0
	elif i%6 == 3:
                a,b = line.split(" ")
	elif i%6 == 4:
		c,b = line.split(" ")
	elif i%6 == 5:
		d,b = line.split(" ")
	elif i%6 == 0:
		log["Time"] = dt
		log["Volts"] = float(a)
                if float(a) < 1.0:
                        print "Power cycle at: ", dt
		log["Amps"] = float(c)
		log["C"] = float(d)
		data.append(log)
	else:
		continue
df = pd.DataFrame(data)
power_cycles = [
               "2018-08-29 13:44:07.473202",
               "2018-08-29 23:58:02.029136",
               "2018-08-29 23:58:56.375937",
               "2018-08-30 00:04:18.729628",
               "2018-08-30 09:59:05.054036",
               "2018-08-30 17:45:15.129030",
               "2018-09-02 17:02:31.759043",
               "2018-09-02 23:12:45.205361",
               "2018-09-02 23:25:35.855088",
               "2018-09-03 08:56:33.679489"]
#print df
for idx,date in enumerate(power_cycles):
                
                power_cycles[idx] = datetime(int(date[:4]),int(date[5:7]),int(date[8:10]),int(date[11:13]),int(date[14:16]),int(date[17:19]))
                plt.axvline(power_cycles[idx], color ='r')
fig = plt.figure()
ax = fig.add_subplot(3, 1, 1)
ax2 = fig.add_subplot(3, 1, 2)
ax3 = fig.add_subplot(3, 1, 3)
ax.plot(df['Time'],df['Volts'])
ax.get_yaxis().get_major_formatter().set_useOffset(False)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
ax.set_ylabel('Volts')
#ax.set_ylim([10.94,10.97])
ax2.plot(df['Time'],df['Amps'])
ax2.set_ylabel('Amps')
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
ax3.plot(df['Time'],df['C'])
plt.gcf().autofmt_xdate()
ax3.set_ylabel('Deg. C')
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
plt.savefig('Plot')
