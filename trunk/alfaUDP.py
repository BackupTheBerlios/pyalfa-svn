#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Biblioteca para gerenciar o Kit Alfa da PNCA <http://www.pnca.com.br>
#
# Autor: Fernando Paolieri Neto <fernando@cronuxs.net>
#          
#

import random
import socket
import time
import re
import signal

MODE_NORMAL  = 0
MODE_CAPTURE = 1

MOTOR_BOTH  = 0
MOTOR_RIGHT = 1
MOTOR_LEFT  = 2

HOST = "localhost"
PORT = 4950

RE_SONAR_READING = "<return>\n[\t ]*<get>([0-9]*)[\t ]*</get>\n</return>"
RE_POSIT_READING = "<return>\n[\t ]*<get>([.0-9-]*);([.0-9-]*);([.0-9-]*)[\t ]*</get>\n</return>"
RE_GET_DEFAULT   = "<return>\n[\t ]*<get>([.0-9-]*)[\t ]*</get>\n</return>"

def handler(signum,frame):
	"""This is a handler function called when a SIGALRM is received, 
	it simply raises a string exception"""

	raise "SocketTimeOut"

class AlfaUDPException:
    def __init__(self, cod):	
        self._cod = cod
    def __cmp__(self, cod):
        return self._cod == cod

class Alfa(object):
    def __init__(self, serial_port = 0, rate = 9600):
        """ Opens the connection with the robot. """
	self._motor_right = 0
        self._motor_left = 0
	self._dest = (HOST, PORT)
	self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	
    def _sendCommand(self, cmd):
        """ Sends a command to the robot. """
        #print cmd
	flag = 1
	while flag:
		try:
			signal.signal(signal.SIGALRM,handler)
			signal.alarm(1)
			
			self.udp.sendto (cmd, self._dest)
			resp = self.udp.recvfrom(1024)[0]
			
			signal.alarm(0)
			flag = 0
		except "SocketTimeOut":
			print "Socket Timeout"
			pass
	
	#print resp
	return resp

    def ping(self):
        return True
    
    def readSensors(self):
        """ Returns a dictionary with the sensor values. """
	#print "readSensors"
	ret = {}
	ret['S1'] = random.randint(0,1) == 0
	ret['S2'] = random.randint(0,1) == 0
	ret['S5'] = random.randint(0,1) == 0
	ret['S6'] = random.randint(0,1) == 0
	ret['MOTERR'] = random.randint(0,1) == 0
	ret['BtEnt'] = random.randint(0,1) == 0
	ret['CPUBat'] = 500 + random.randint(0,500)
	ret['MOTBat'] = 800 + random.randint(0,200)
	
	def get_sonar(n):
		reg = re.compile (RE_SONAR_READING)
		cmd  = "<program><get><name>getSonarRange</name><par>%d</par></get></program>" % n
		resp = reg.findall(self._sendCommand(cmd))[0]
		resp = float(resp)
		#resp = resp / 5000
		#return resp * 1024
		if resp < 0 : resp += 360
		if (resp > 1024):	return 1024
		else:			return resp
	
	def get_position():
		reg = re.compile (RE_POSIT_READING)
		cmd = "<program><get><name>getPosition</name></get></program>"
		resp = reg.findall(self._sendCommand(cmd))[0]
		resp = [float(i) for i in resp]
		return resp
	def get_robot_length():
		reg = re.compile (RE_GET_DEFAULT)
		cmd = "<program><get><name>getRobotLength</name></get></program>"
		resp = reg.findall(self._sendCommand(cmd))
		resp = float(resp[0])
		return resp
	def get_robot_width():
		reg = re.compile (RE_GET_DEFAULT)
		cmd = "<program><get><name>getRobotWidth</name></get></program>"
		resp = reg.findall(self._sendCommand(cmd))
		resp = float(resp[0])
		return resp
	def get_velocity():
		reg = re.compile (RE_GET_DEFAULT)
		cmd = "<program><get><name>getVel</name></get></program>"
		resp = reg.findall(self._sendCommand(cmd))
		resp = float(resp[0])
		return resp
	
	ret['S3'] = get_sonar(3)
	ret['S4'] = get_sonar(4)
	ret['S7'] = get_sonar(11)
	ret['S8'] = get_sonar(12)
	ret['POS'] = get_position()
	ret['LEN'] = get_robot_length()
	ret['WID'] = get_robot_width()
	ret['VEL'] = get_velocity()

	return ret

    def setServoTable(self, servo, table):
        print "setServoTable"
	
    def getServoApproximateAngle(self, servo, angle):
        return 0
    
    def moveServo(self, servo, angle):
    	print "moveServo"

    def identify(self):
        return { "name"    : "O cara",
                 "version" : "1.2",
                 "revision": "BAAD"}

    def motorSpeed(self, speed, motor = MOTOR_BOTH):
	speed = int(speed)
        if not (-10 <= speed <= 10):
            raise AlfaException("InvalidSpeed")

	if not (MOTOR_BOTH <= motor <= MOTOR_LEFT):
            raise AlfaException("InvalidMotor")
		
        if motor == MOTOR_BOTH or motor == MOTOR_LEFT:
            self._motor_left = speed

        if motor == MOTOR_BOTH or motor == MOTOR_RIGHT:
            self._motor_right = speed
	
	if self._motor_right == self._motor_left :
		cmd = "<program><async-op><name>setVel</name><par>%d</par></async-op></program>" % (speed*100)
        	resp = self._sendCommand(cmd)
		cmd = "<program><async-op><name>setRotVel</name><par>%d</par></async-op></program>" % 0
        	resp = self._sendCommand(cmd)
		
	elif self._motor_right == 0 and self._motor_left != 0 :
		cmd = "<program><async-op><name>setVel</name><par>%d</par></async-op></program>" % 0
        	resp = self._sendCommand(cmd)
		cmd = "<program><async-op><name>setRotVel</name><par>%d</par></async-op></program>" % (speed*-1000)
        	resp = self._sendCommand(cmd)
		
	elif self._motor_right != 0 and self._motor_left == 0 :
		cmd = "<program><async-op><name>setVel</name><par>%d</par></async-op></program>" % 0
        	resp = self._sendCommand(cmd)
		cmd = "<program><async-op><name>setRotVel</name><par>%d</par></async-op></program>" % (speed*1000)
        	resp = self._sendCommand(cmd)
	else :
		cmd = "<program><async-op><name>setVel</name><par>%d</par></async-op></program>" % (abs(self._motor_right) - abs(self._motor_left))
		resp = self._sendCommand(cmd)
		cmd = "<program><async-op><name>setRotVel</name><par>%d</par></async-op></program>" % (self._motor_left - self._motor_right)
        	resp = self._sendCommand(cmd)

    def motorForward(self, speed):
        self.motorSpeed(speed)
	
    def motorBackward(self, speed):
        self.motorForward(-speed)

    def motorLeft(self, speed):
        self.motorSpeed(   speed,MOTOR_LEFT)
        self.motorSpeed( - speed,MOTOR_RIGHT)
	 
    def motorRight(self, speed):
        self.motorSpeed( - speed,MOTOR_LEFT)
        self.motorSpeed(   speed,MOTOR_RIGHT)
	 
    def motorStop(self):
        self.motorSpeed(0)
	
    def sound(self, frequency, duration):
        self.soundStart(frequency)
        time.sleep(duration)
        self.soundStop()
	
    def soundStart(self, frequency):
        print "soundStart"
	
    def soundStop(self):
	print "soundStop"
	
    def __del__(self):
	self.udp.close()

if __name__ == '__main__':
    #l = Alfa( serial_port = "/dev/ttyUSB0", rate = 57600)
    l = Alfa( serial_port = "/dev/ttyUSB0")
    print "robo responde =>", l.ping()
    print "sensores      =>", l.readSensors()
    print "identificacao =>", l.identify()
    #l.motorSpeed(10)
   #print "anda (potencia 10)"
    #time.sleep(2)
    #l.motorSpeed(0)
    #print "som por 2 segundos"
    #l.sound(50, 2)

    try:
        while 1: 
            time.sleep(0.00001)
            sensors = l.readSensors()
            for sensor in sorted(sensors):
                print sensor, sensors[sensor]
    except KeyboardInterrupt :
        del(l)
        print "Bye" 

