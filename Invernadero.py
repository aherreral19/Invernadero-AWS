from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import RPi.GPIO as GPIO
import dht11
import time
import datetime
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import logging
import argparse
import json

pin=7  
GPIO.setmode(GPIO.BOARD) 
GPIO.setup(pin, GPIO.OUT)

# A random programmatic shadow client ID.
SHADOW_CLIENT = "myIotThing"
# The unique hostname that &IoT; generated for
# this device.
HOST_NAME = "a21eej1uzh2ht6-ats.iot.us-east-2.amazonaws.com"
# The relative path to the correct root CA file for &IoT;,
# which you have already saved onto this device.
ROOT_CA = "Amazon_Root_CA_1.pem"
# The relative path to your private key file that
# &IoT; generated for this device, which you
# have already saved onto this device.
PRIVATE_KEY = "5e45e96e46-private.pem.key"
# The relative path to your certificate file that
# &IoT; generated for this device, which you
# have already saved onto this device.
CERT_FILE = "5e45e96e46-certificate.pem.crt"
# A programmatic shadow handler name prefix.
SHADOW_HANDLER = "myIotThing"
# Automatically called whenever the shadow is updated.

AllowedActions = ['both', 'publish', 'subscribe']

# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    if (message.payload=="REGAR"):
	GPIO.output(pin,GPIO.HIGH) 
    	time.sleep(5)
    	GPIO.output(pin,GPIO.LOW)
    else:
	GPIO.output(pin,GPIO.LOW)
    print("--------------\n\n")


# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--mode", action="store", dest="mode", default="both",
                    help="Operation modes: %s"%str(AllowedActions))
parser.add_argument("-M", "--message", action="store", dest="message", default="OFF",
                    help="Message to publish")

args = parser.parse_args()
#host = args.host
host=HOST_NAME
#rootCAPath = args.rootCAPath
rootCAPath=ROOT_CA
#certificatePath = args.certificatePath
certificatePath=CERT_FILE
#privateKeyPath = args.privateKeyPath
privateKeyPath=PRIVATE_KEY
#port = args.port
port =8883
#useWebsocket = args.useWebsocket
useWebsocket=False
#clientId = args.clientId
clientId="basicPubSub"
#topic = args.topic
topic="my/Invernadero"

# Configure logging

#logger = logging.getLogger("AWSIoTPythonSDK.core")
#logger.setLevel(logging.DEBUG)
#streamHandler = logging.StreamHandler()
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#streamHandler.setFormatter(formatter)
#logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
if args.mode == 'both' or args.mode == 'subscribe':
    myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

def myShadowUpdateCallback(payload, responseStatus, token):
	print()
	print('UPDATE: $aws/things/' + SHADOW_HANDLER +
	'/shadow/update/#')
	print("payload = " + payload)
	print("responseStatus = " + responseStatus)
	print("token = " + token)
# Create, configure, and connect a shadow client.
myShadowClient = AWSIoTMQTTShadowClient(SHADOW_CLIENT)
myShadowClient.configureEndpoint(HOST_NAME, 8883)
myShadowClient.configureCredentials(ROOT_CA, PRIVATE_KEY,
CERT_FILE)
myShadowClient.configureConnectDisconnectTimeout(10)
myShadowClient.configureMQTTOperationTimeout(5)
myShadowClient.connect()
# Create a programmatic representation of the shadow.
myDeviceShadow = myShadowClient.createShadowHandlerWithName(
SHADOW_HANDLER, True)

# Represents the GPIO21 pin on the Raspberry Pi.
# Use the GPIO BCM pin numbering scheme.

instance = dht11.DHT11(pin=11)
SPI_PORT   = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
# Receive input signals through the pin.
while True:
    result = instance.read()
    if result.is_valid():
        #print("Last valid input: " + str(datetime.datetime.now()))
        print("\nTemperatura ambiente: %d C" % result.temperature)
        print("Humedad ambiente: %d %%" % result.humidity)
        value = mcp.read_adc(0)
        Ground_humidity = 100-value*100/1024
        #value1 = mcp.read_adc(1)
        #if Ground_humidity > 80:
            #print('Channel 0: {0}'.format(value))
        print("Humedad en la tierra alta \n"'Channel 0: {}'.format(Ground_humidity)+"%\n")
##        elif Ground_humidity < 40:
##            #print('Channel 0: {0}'.format(value))
##            print("Humedad en la tierra baja \n"'Channel 0: {}'.format(Ground_humidity)+ "%\n")
        
        #---------AWS condiciones--------------#
        
        if result.temperature > 10 and result.temperature < 30 and result.humidity < 80 and result.humidity > 40 and Ground_humidity < 80 and Ground_humidity > 40:
		myDeviceShadow.shadowUpdate(
		'{"state":{"reported":{"Humedad_Ambiente":"Okay","Temperatura_Ambiente":"Okay","Humedad_Tierra":"Okay"}}}',
		myShadowUpdateCallback, 5)
        else:
            myDeviceShadow.shadowUpdate(
            '{"state":{"reported":{"RegarPlantas":"Regar"}}}',
            myShadowUpdateCallback, 5)
##            if result.temperature < 10 :
##		Temp = "Humedad_Ambiente":"low"
##	    else:
##                Temp = ""
##                
##	    if result.humidity < 40 :
##                Hum_Amb = "Temperatura_Ambiente":"low"
##            else:
##                Hum_Amb = ""
##                
##            if Ground_humidity < 40 : 
##                Hum_Tierra = "Humedad_Tierra":"low"   
##            else :
##                Temp = ""
##                Hum_Amb = ""
##                Hum_Tierra = ""
                
            
    #print('Channel 1: {0}'.format(value1))
        time.sleep(5)
    
    
    
    
    
    