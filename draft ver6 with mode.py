import lcddriver
lcd = lcddriver.lcd()
lcd.lcd_display_string("Initializing... 0%",1)
lcd.lcd_display_string("Analog communication",2)
import Adafruit_ADS1x15 as ads
import RPi.GPIO as GPIO  
import time
import datetime
pumpPin = 38
vavlePin = 40
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pumpPin,GPIO.OUT)
GPIO.setup(vavlePin,GPIO.OUT)
adc1 = ads.ADS1115(address=0x48)
GAIN=1
#########################################Global VAR
pumpState = "OFF"
vavleState = "OFF"
pumpConfig = "A"
vavleConfig = "A"
dispStatus = "ON"
dispTime = "ON"
#########################################Freebiard & line notify
import paho.mqtt.client as mqtt 
import json
import random
myData = { "ID" : 123, "tankA" : "N", "tankB" : "M", "tds" : -16, "pump" : "on", "vavle" : "on"}
NETPIE_HOST = "broker.netpie.io"
CLIENT_ID = ""
DEVICE_TOKEN = ""
def on_connect(client, userdata, flags, rc):
    print("NETPIE connecting: {}".format(mqtt.connack_string(rc)))
    client.subscribe("@shadow/data/updated")
def on_subscribe(client, userdata, mid, granted_qos):
    print("successful")
def on_message(client, userdata, msg):
    data = str(msg.payload).split(",")
    #print(data,'end of data')
    
    key = data[1].split("{")[1].split(":")[0].split('"')[1]
    value = data[1].split("{")[1].split(":")[1].split('}')[0].split('"')[1]
    if(key == "pumpConfig"):
        global pumpConfig
        pumpConfig = value
        print("PumpCFG update")
    elif(key == "vavleConfig"):
        global vavleConfig
        vavleConfig = value
        print("vavleCFG update")
    elif(key == "led"):
        global dispStatus
        dispStatus = value
        print("BacklightCFG update")
    elif(key == "time"):
        global dispTime
        dispTime = value
        print("dispTimeCFG update")
lcd.lcd_display_string("NETPIE connection    ",2)
client = mqtt.Client(protocol=mqtt.MQTTv311,client_id=CLIENT_ID, clean_session=True)
client.username_pw_set(DEVICE_TOKEN)
lcd.lcd_display_string("Initializing... 10%",1)
client.on_connect = on_connect
lcd.lcd_display_string("Initializing... 20%",1)
client.on_message = on_message
lcd.lcd_display_string("Initializing... 40%",1)
client.connect(NETPIE_HOST, 1883)
lcd.lcd_display_string("Initializing... 50%",1)
client.loop_start()
#########################################log
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
lcd.lcd_display_string("Initializing... 50%",1)
lcd.lcd_display_string("Gspread API         ",2)
SheetName = "API test"
GSheet_OAUTH_JSON = ""
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(GSheet_OAUTH_JSON, scope)
lcd.lcd_display_string("Initializing... 60%",1)
clientG = gspread.authorize(credentials)
lcd.lcd_display_string("Initializing... 70%",1)
worksheet = clientG.open(SheetName).sheet1
lcd.lcd_display_string("Initializing... 80%",1)
row = ["Time","Fresh tank","Using tank","TDS"]
index = 2
worksheet.insert_row(row,index)
lcd.lcd_display_string("Initializing...90%",1)
print("Gspread API connected")
#########################################

def waterLevel(k):
    value = adc1.read_adc(k,gain=GAIN)
    #print("Water sensor:",k," level:",value)
    if value < 15000:
        return "GOOD"
    elif value < 22000:
        return "AL FULL"
    else:
        return "FULL"
def waterNLevel():
    value = adc1.read_adc(0,gain=GAIN)
    if(value > 1000):
        #print("Water N detect")
        return "GOOD"
    else:
        #print("Water N not detect")
        return "EMPTY"
def tdsLevel():
    value = adc1.read_adc(3,gain=GAIN)
    value = value/16
    #print("TDS level:",value)
    return value
def pump_on():
    GPIO.output(pumpPin,GPIO.LOW)
    global pumpState
    pumpState = "ON"
def pump_off():
    GPIO.output(pumpPin,GPIO.HIGH)
    global pumpState
    pumpState = "OFF"
def vavle_on():
    GPIO.output(vavlePin,GPIO.LOW)
    global vavleState
    vavleState = "ON"
def vavle_off():
    GPIO.output(vavlePin,GPIO.HIGH)
    global vavleState
    vavleState = "OFF"
    
while True:
    #Obtain value
    tds = tdsLevel()#Fresh tank (tankB)
    w1 = waterLevel(1)#Fresh tank
    w2 = waterLevel(2)#Using tank (tankA)
    w3 = waterNLevel()#Using tank
    if w1 == "GOOD" and tds < 10:
        w1 = "EMPTY"
    if w2 == "GOOD" and w3 == "EMPTY":
        w2 = "EMPTY"
    #Operation
    msg = ""
    if(pumpConfig == "A"):
        if w2 == "EMPTY":
            msg = "PUMPING"
            pump_on()
        elif w2 == "AL FULL" or w2 == "FULL":
            pump_off()
    elif(pumpConfig == "F"):
        msg = "EDGE-OPER"
        if w2 == "GOOD":
            pump_on()
        elif w2 == "AL FULL" or w2 == "FULL":
            pump_off()
    elif(pumpConfig == "P"):
        msg = "PUMP-OFF"
        pump_off()
    else:
        print("pump state error")
    
    if(vavleConfig == "A"):
        if w1 == "EMPTY":
            vavle_on()
            msg += " REFILL"
        elif w1 == "AL FULL" or w1 == "FULL":
            vavle_off()
    elif(vavleConfig == "M"):
        msg += " MAN-VAVLE"
        vavle_on()
    elif(vavleConfig == "P"):
        msg = " VAVLE-OFF"
        vavle_off()
    else:
        print("vavle state error")
        
    
    #Disp
    lcd.lcd_clear()
    lcd.lcd_display_string("Fresh tank: "+w1,1)
    lcd.lcd_display_string("Using tank: "+w2,2)
    if(dispTime == "ON"):
        lcd.lcd_display_string("TDS: "+str(int(tds))+"      "+datetime.datetime.now().strftime("%H:%M:%S"),3)
    else:
        lcd.lcd_display_string("TDS: "+str(int(tds)),3)
    if(dispStatus == "ON"):
        lcd.lcd_display_string(msg,4)
    #LOG
    currentTime = datetime.datetime.now().strftime("%H:%M:%S")
    worksheet.append_row([currentTime,w1,w2,tds])
    #Freeboard
    myData['tankA'] = w1
    myData['tankB'] = w2
    myData['tds'] = tds
    myData['pump'] = pumpState
    myData['vavle'] = vavleState
    myData['pumpConfig'] = pumpConfig
    myData['vavleConfig'] = vavleConfig
    myData['time'] = dispTime
    myData['led'] = dispStatus
    client.publish("@shadow/data/update",json.dumps({"data": myData}), 1)
    
    time.sleep(0.5)




