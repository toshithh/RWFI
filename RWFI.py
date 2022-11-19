import subprocess
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import time
import os


def read_file(fn=f"out-05.csv"):
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


################################### WEB MAC ADDRESSES ###################################

firefox_options = Options()
firefox_options.add_argument("--headless")

unm = input("Enter registered email: ")
pwd = input("Enter password: ")
os.system("clear")
print("processing...")

driver = webdriver.Firefox(options=firefox_options)
driver.get("http://192.168.0.188:8000")

username_field = driver.find_element(By.NAME, "username")
password_field = driver.find_element(By.NAME, "password")
username_field.send_keys(unm)
password_field.send_keys(pwd)
time.sleep(1)
password_field.submit()
time.sleep(1)

driver.get('http://192.168.0.188:8000/mac_token')
s = driver.find_element(By.TAG_NAME, "body")
macs = s.text
macs = macs.replace("\n",';')
macs = macs.split(';')
rnm = input("Enter the name of your wifi router(Type carefully): ")


################################### WiFi adapter name ##########################################

wifi = subprocess.Popen("""iw dev | awk '$1=="Interface"{print $2}'""", shell=True, stdout=subprocess.PIPE).stdout
wifi = wifi.read().decode().split('\n')
wifi = wifi[0].strip()
print("The cleansing is starting")
if "mon" not in wifi:
    temp = subprocess.Popen(f"sudo airmon-ng start {wifi}", shell=True, stdout=subprocess.PIPE).stdout
    time.sleep(5)
else:
    wifi = wifi.replace('mon','')

os.system(f"sudo timeout 30 airodump-ng -w remove --write-interval 1 -o csv {wifi}mon")
time.sleep(31)


############################### Derive MAC ADDRESSES ####################################

stations, APs = read_file(f"remove-01.csv")
rmacs = []
for i in range(len(APs['essid'])):
    if str(APs['essid'][i].strip()) == rnm:
        rmacs.append((APs['router'][i].strip(), int(APs['pwr'][i].strip()), APs['channel'][i].strip()))
rmacs.sort(key = lambda x: x[1])
rmac = rmacs[-1]

os.system(f"sudo iwconfig {wifi}mon channel {rmac[2]}")

while 1:
    for x in stations['station']:
        if x.strip() in macs:
            pass
        else:
            os.system(f"aireplay-ng --deauth 1 -a {rmac[0]} -c {x.strip()} {wifi}mon")
