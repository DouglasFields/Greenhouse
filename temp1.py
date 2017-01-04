# Very first attempt at programming python

import matplotlib
matplotlib.use('TkAgg')

#import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

import sys
import os
#import threading
#import pandas as pd

import requests

import paho.mqtt.client as mqtt

if sys.platform.startswith('linux'):
    import Adafruit_DHT as dht
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(40, GPIO.OUT)
    GPIO.output(40, GPIO.LOW)


from datetime import datetime

if(sys.version_info[0]<3):
   import Tkinter as tk
else:
   import tkinter as tk

import csv

# Used for notifications with picture
#import pyimgur
#import picamera
from twilio.rest import TwilioRestClient

import accounts as acc

# initalize the Twilio client
client = TwilioRestClient(acc.TWILIO_SID, acc.TWILIO_AUTH_TOKEN)

# directory to save the snapshot in
#IMAGE_DIR = "./pics/"

# initialize imgur client
#im = pyimgur.Imgur(CLIENT_ID)

# name and dimentsions of snapshot image
#IMG = " "
#IMG_WIDTH = 800
#IMG_HEIGHT = 600

root = tk.Tk()

updt=tk.StringVar()
upd=tk.StringVar()
upt=tk.StringVar()
intempstring=tk.StringVar()
inhumidstring=tk.StringVar()
outtempstring=tk.StringVar()
outhumidstring=tk.StringVar()
low_thresh=tk.IntVar(value=30)
high_thresh=tk.IntVar(value=100)

updt.set(datetime.now().strftime("%a, %d %b %Y, %I:%M:%S %p"))
upd.set(datetime.now().strftime("%a, %d %b %Y"))
upt.set(datetime.now().strftime("%I:%M:%S %p"))

if os.path.exists("ghtemphumid.csv"):
#   print('CSV File exists!')
   csvfile = open('ghtemphumid.csv', 'a+')
   fieldnames = ['Date_Time', 'Inside_Temp', 'Inside_Humid', 'Outside_Temp', 'Outside_Humid' ]
   writer = csv.DictWriter(csvfile, dialect='excel', fieldnames=fieldnames)
   r = mlab.csv2rec(csvfile.name)
   r.sort()
   r = r[-576:]  # get the last 2 days of entries

else:
#   print('CSV File does not exist! Creating new file.')
   csvfile = open('ghtemphumid.csv', 'w+')
   fieldnames = ['Date_Time', 'Inside_Temp', 'Inside_Humid', 'Outside_Temp', 'Outside_Humid' ]
   writer = csv.DictWriter(csvfile, dialect='excel', fieldnames=fieldnames)
   writer.writeheader()
   writer.writerow({'Date_Time': updt.get(), 'Inside_Temp': intempstring.get(), 'Inside_Humid': inhumidstring.get(), 'Outside_Temp': outtempstring.get(), 'Outside_Humid': outhumidstring.get() })
   csvfile.flush()
   r = mlab.csv2rec(csvfile.name)
   r.sort()
   r = r[-576:]  # get the last 2 days of entries
   
intemp = r.inside_temp[len(r)-1]
inhumid = r.inside_humid[len(r)-1]
outtemp = r.outside_temp[len(r)-1]
outhumid = r.outside_humid[len(r)-1]

intempstring.set('{:.1f}'.format(intemp))
inhumidstring.set('{:.1f}'.format(inhumid))
outtempstring.set('{:.1f}'.format(outtemp))
outhumidstring.set('{:.1f}'.format(outhumid))

was_good = False
if (intemp > low_thresh.get() and intemp < high_thresh.get()):
    was_good = True


def on_connect(mqttclient, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    mqttclient.subscribe("Greenhouse/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(mqttclient, userdata, msg):
    global intemp, inhumid
    print(msg.topic+" "+str(msg.payload))
    if msg.topic == "Greenhouse/temp":
        intemp = float(msg.payload)
        intempstring.set('{:.1f}'.format(intemp))
    elif msg.topic == "Greenhouse/humid":
        inhumid = float(msg.payload)
        inhumidstring.set('{:.1f}'.format(inhumid))

mqttclient = mqtt.Client()
mqttclient.on_connect = on_connect
mqttclient.on_message = on_message

mqttclient.connect(acc.DDNS_URL, acc.DDNS_PORT, acc.DDNS_TO)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
mqttclient.loop_start()
    
class LED(tk.Frame):
    """A Tkinter LED Widget.
    a = LED(root,10)
    a.set(True)
    current_state = a.get()"""
    ON_STATE = 1
    OFF_STATE = 0
    
    def __init__(self,master,size=10,**kw):
        self.size = size
        self.fillcolor = 'white'
        tk.Frame.__init__(self,master,width=size,height=size)
        self.configure(**kw)
        self.state = LED.OFF_STATE
        self.c = tk.Canvas(self,width=self['width'],height=self['height'])
        self.c.grid()
        self.led = self._drawcircle((self.size/2)+1,(self.size/2)+1,(self.size-1)/2)
    def _drawcircle(self,x,y,rad):
        """Draws the circle initially"""
        return self.c.create_oval(x-rad,y-rad,x+rad,y+rad,width=rad/5,fill=self.fillcolor,outline='black')
    def _change_color(self):
        """Updates the LED colour"""
        if self.state == LED.ON_STATE:
            color=self.fillcolor
        else:
            color="white"
        self.c.itemconfig(self.led, fill=color)
    def set(self,state):
        """Set the state of the LED to be True or False"""
        self.state = state
        self._change_color()
    def get(self):
        """Returns the current state of the LED"""
        return self.state


class App(tk.Frame):
   def __init__(self,parent=None, **kw):
       tk.Frame.__init__(self,parent,**kw)
       self.parent = parent
       self.grid()
       self.labels()
       self.exitButton()
       self.fig, self.ax = plt.subplots()
       self.fig.size=(2, 2)
       self.fig.dpi=45
       self.canvas = FigureCanvasTkAgg(self.fig, master=self)
       self.canvas.get_tk_widget().grid(row=2,column=3,rowspan=3,columnspan=2)
       self.low_slide = tk.Scale(self, label='Low Thresh', from_=0, to=50, orient=tk.HORIZONTAL, variable=low_thresh)
       self.high_slide = tk.Scale(self, label='High Thresh', from_=50, to=100, orient=tk.HORIZONTAL, variable=high_thresh)
       self.low_slide.grid(row=6,column=3)
       self.high_slide.grid(row=6,column=4)
       self.led_low = LED(self,20)
       self.led_low.fillcolor='blue'
       self.led_low.grid(row=5,column=3)
       self.led_good = LED(self,20)
       self.led_good.fillcolor='green'
       self.led_good.grid(row=5,column=4)
       self.led_high = LED(self,20)
       self.led_high.fillcolor='red'
       self.led_high.grid(row=5,column=5)
       self.led_good.set(1)
       self.led_high.set(0)
       self.led_low.set(0)
       self.plottemp()
       self.reads = 0
       self.first_read = True
       self.ReadTemp()
       self.WriteTemp()
       self.update()

   def onClose(self):
       """This is used to run the Rpi.GPIO cleanup() method to return pins to be an input
       and then destory the app and its parent."""
       global csvfile
#     Clean up the GPIO states on the Raspberry Pi if running on it
       if sys.platform.startswith('linux'):
         try:
           GPIO.cleanup()
         except RuntimeWarning as e:
           print(e)
    # Close files
       csvfile.close()
       self.destroy()
       self.parent.destroy()
       mqttclient.loop_stop()
  
    
   def labels(self):
       
       self.datelabel = tk.Label(self, text = "Date = ")
       self.datepost = tk.Label(self, textvariable = upd)
       self.timelabel = tk.Label(self, text = "Time = ")
       self.timepost = tk.Label(self,textvariable = upt)
       self.intemplabel = tk.Label(self, text = "Inside \n Temperature = ", fg='blue')
       self.intemppost = tk.Label(self,textvariable = intempstring)
       self.inhumidlabel = tk.Label(self, text = "Inside \n Humidity = ", fg='green')
       self.inhumidpost = tk.Label(self,textvariable = inhumidstring)
       self.outtemplabel = tk.Label(self, text = "Outside \n Temperature = ", fg='red')
       self.outtemppost = tk.Label(self,textvariable = outtempstring)
       self.outhumidlabel = tk.Label(self, text = "Outside \n Humidity = ", fg='yellow')
       self.outhumidpost = tk.Label(self,textvariable = outhumidstring)
       self.timelabel.config(font=("Helvetica", 18))
       self.datelabel.config(font=("Helvetica", 18))
       self.timepost.config(font=("Helvetica", 18))
       self.datepost.config(font=("Helvetica", 18))
       self.intemplabel.config(font=("Helvetica", 18))
       self.inhumidlabel.config(font=("Helvetica", 18))
       self.outtemplabel.config(font=("Helvetica", 18))
       self.outhumidlabel.config(font=("Helvetica", 18))
       self.intemppost.config(font=("Helvetica", 50))
       self.inhumidpost.config(font=("Helvetica", 50))
       self.outtemppost.config(font=("Helvetica", 50))
       self.outhumidpost.config(font=("Helvetica", 50))
       self.datelabel.grid(row=1,column=1)
       self.datepost.grid(row=1,column=2)
       self.timelabel.grid(row=1,column=3)
       self.timepost.grid(row=1,column=4)
       self.intemplabel.grid(row=2,column=1)
       self.intemppost.grid(row=2,column=2)
       self.inhumidlabel.grid(row=3,column=1)
       self.inhumidpost.grid(row=3,column=2)
       self.outtemplabel.grid(row=4,column=1)
       self.outtemppost.grid(row=4,column=2)
       self.outhumidlabel.grid(row=5,column=1)
       self.outhumidpost.grid(row=5,column=2)

   def exitButton(self):
       self.exitButton = tk.Button(self, text = "Exit", command = self.onClose, height = 2, width = 6)
       self.exitButton.grid(row=6,column=1)
       
   def plottemp(self):
       global r
       self.ax.clear()
       self.ax.plot(r.date_time, r.inside_temp, 'bo-')
       self.ax.plot(r.date_time, r.inside_humid, 'g+-')
       self.ax.plot(r.date_time, r.outside_temp, 'r+-')
       self.ax.plot(r.date_time, r.outside_humid, 'y+-')
       self.fig.autofmt_xdate()
       self.canvas.show()


   def update(self):
       """Runs every 100ms to update the state of the GPIO inputs"""
       global updt
       global upd
       global upt
       updt.set(datetime.now().strftime("%a, %d %b %Y, %I:%M:%S %p"))
       upd.set(datetime.now().strftime("%a, %d %b %Y"))
       upt.set(datetime.now().strftime("%I:%M:%S %p"))
       self.plottemp()
       self._timer = self.after(1000,self.update)

   def ReadTemp(self):
       global intempstring
       global inhumidstring
       global outtempstring
       global outhumidstring
       global intemp
       global inhumid
       global outtemp
       global outhumid
       global was_good
       global first_read
       if sys.platform.startswith('linux'):
# Read DHT22
           dht_humid,dht_temp = dht.read_retry(dht.DHT22,4)
           dht_temp = (9./5.)*dht_temp +32.
# Check to make sure the DHT read reasonable values          
           if (dht_temp < 200 and dht_humid < 100):
               intemp = dht_temp
               inhumid = dht_humid
       else:
           intemp += 1.
           inhumid += 1.
#  Get current conditions from Weather Underground
       if self.reads == 0:
          req = requests.get("http://api.wunderground.com/api/9a9de324205236f1/conditions/q/NM/pws:KNMALBUQ360.json")
          data = req.json()
          try:
            outtemp = float(data['current_observation']['temp_f'])
            outhumid = float(data['current_observation']['relative_humidity'][:-1])
          except:
            print("Keyerror, keeping last value at "+updt.get())
          self.reads += 1
       elif self.reads == 59:
           self.reads = 0
       else:
           self.reads += 1

       intempstring.set('{:.1f}'.format(intemp))
       inhumidstring.set('{:.1f}'.format(inhumid))
       outtempstring.set('{:.1f}'.format(outtemp))
       outhumidstring.set('{:.1f}'.format(outhumid))
       
# Check the inside temp against thresholds, set led colors and send a notification if state changed
       if (intemp > high_thresh.get()):
           if (was_good and not self.first_read):
             was_good = False
             self.led_high.set(1)
             self.led_good.set(0)
             self.led_low.set(0)
             client.messages.create(
		   to = acc.TO_PHONE,
		   from_ = acc.FROM_PHONE,
		   body = "Temerature greater than "+str(high_thresh.get()),
#			media_url=uploaded_image.link,
		   )
       elif (intemp < low_thresh.get()):
           if (was_good and not self.first_read):
             was_good = False
             self.led_low.set(1)
             self.led_high.set(0)
             self.led_good.set(0)
             client.messages.create(
		   to = acc.TO_PHONE,
		   from_ = acc.FROM_PHONE,
		   body = "Temerature less than "+str(low_thresh.get()),
#			media_url=uploaded_image.link,
		   )
       else:
           if (not was_good and not self.first_read):
              was_good = True
              self.led_good.set(1)
              self.led_high.set(0)
              self.led_low.set(0)
              client.messages.create(
			to = acc.TO_PHONE,
			from_ = acc.FROM_PHONE,
			body="Temerature back to good range",
#			media_url=uploaded_image.link,
		   )
              
       self.first_read = False
       self._timer = self.after(5000,self.ReadTemp)

   def WriteTemp(self):
       global r
       global csvfile
       writer.writerow({'Date_Time': updt.get(), 'Inside_Temp': intempstring.get(), 'Inside_Humid': inhumidstring.get(), 'Outside_Temp': outtempstring.get(), 'Outside_Humid': outhumidstring.get() })
       csvfile.flush()
       r = mlab.csv2rec(csvfile.name)
       r.sort()
       r = r[-576:]  # get the last day of entries
       self._timer = self.after(300000,self.WriteTemp)

def main():
   global updt
   global upd
   global upt
   global stopFlag
   
   root.title("Greenhouse")

   a = App(root)

   """When the window is closed, run the onClose function."""
   root.protocol("WM_DELETE_WINDOW",a.onClose)
   root.geometry('800x600')
   root.resizable(True,True)

   root.mainloop()
 

if __name__ == '__main__':
   main()



