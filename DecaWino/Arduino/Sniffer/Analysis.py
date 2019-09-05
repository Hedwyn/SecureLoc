import matplotlib.pyplot as plt
import statistics as st

LOGS = 'SnifferLogs.txt'
DWM1000_TIMEBASE = 15.65E-6 #us
reply_times =[]
clk_times =[]
with open(LOGS) as f:
    for line in f:
        if line[0] == '$':
            clk_ts = int(line[1:])
            clk_times.append(clk_ts)
            dw_time = DWM1000_TIMEBASE * clk_ts
            reply_times.append(dw_time)

print(st.mean(clk_times))
fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot([i for i in range(len(reply_times))],reply_times)

plt.show()
            
