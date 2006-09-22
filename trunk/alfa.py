#!/usr/bin/python
#
# Biblioteca para gerenciar o Kit Alfa da PNCA <http://www.pnca.com.br>
#
# Autores: Leandro Augusto Fogolin Pereira <leandro@linuxmag.com.br>
#          Fernando Paolieri Neto <fernando@cronuxs.net>
#

import serial
import time

MODE_NORMAL  = 0
MODE_CAPTURE = 1

MOTOR_BOTH  = 0
MOTOR_RIGHT = 1
MOTOR_LEFT  = 2

SERVO_ANGLE_TABLE = { 
  'A': { 0: 15, 15: 21, 30: 27, 45: 33, 60: 39, 75: 45, 90: 49, 105: 57,
         120: 63, 135: 69, 150: 75, 165: 78, 180: 81 },
  'B': { 0: 15, 15: 21, 30: 27, 45: 33, 60: 39, 75: 45, 90: 49, 105: 57,
         120: 63, 135: 69, 150: 75, 165: 78, 180: 81 },
  'C': { 0: 15, 15: 21, 30: 27, 45: 33, 60: 39, 75: 45, 90: 49, 105: 57,
         120: 63, 135: 69, 150: 75, 165: 78, 180: 81 },
  'D': { 0: 15, 15: 21, 30: 27, 45: 33, 60: 39, 75: 45, 90: 49, 105: 57,
         120: 63, 135: 69, 150: 75, 165: 78, 180: 81 }
}

SERVO = { 'A': 'o' , 'B': 'p', 'C': 'q', 'D': 'r'}

class AlfaException:
  def __init__(self, cod):
    self._cod = cod
  def __cmp__(self, cod):
    return self._cod == cod

class Alfa(object):
  def __init__(self, serial_port = '/dev/ttyS0'):
    """ Opens the connection with the robot. """

    self._mode = MODE_NORMAL
    self._motor_right = 0
    self._motor_left = 0
    self._sound = False

    try:
      self._serial = serial.Serial(port = serial_port)
      self._serial.timeout = 0.1
    except serial.serialutil.SerialException:
      raise AlfaException("SerialPortError")

    if not self.ping():
      raise AlfaException("RobotNotResponding")

  def _setMode(self, mode):
    """ Sets the current operating mode. Raises AlfaException("InvalidMode") on invalid
    modes, does nothing if mode is current. """
    """
    if self._mode == mode:
      return
    elif mode == MODE_CAPTURE:
      self._sendCommand("Ms")
      self._mode = mode
    elif mode == MODE_NORMAL:
      self._sendCommand("Mf")
      self._mode = mode
    else:
      raise AlfaException("InvalidMode")
      
    
    Esse codigo aqui eu nao consigo entender... pode explicar depois pq nao pode ser
    do jeito que escrevi acima?   -- Leandro
    """
    if self._mode == mode: return
    if self._motor_right != 0 or self._motor_left != 0: 
      raise AlfaException("MotorOnError")
    
    if self._sound:
      raise AlfaException("SoundOnError")
    
    if self._mode == MODE_CAPTURE:
      self._sendCommand("Mf")
      self._mode = MODE_NORMAL
      self._setMode(mode)
       
    elif self._mode == MODE_NORMAL:
      if mode == MODE_CAPTURE:
        self._sendCommand("Ms")
	self._mode = mode
    """
    da maneira que estava e possivel adcionar novos modos com facilidade! -- Fernando
	"""

  def _sendCommand(self, cmd):
    """ Sends a command to the robot. """
    self._serial.flushInput()
    self._serial.write("%s\r" % cmd)
    self._serial.flushOutput()
    time.sleep(0.05)
  
  def _readResponse(self, bufsize = 10000):
    return self._serial.read(bufsize)
  
  def ping(self):
    """ Returns True if the robot is responding. """

    self._setMode(MODE_NORMAL)
    self._sendCommand("ping")
    return "pong" in self._readResponse()

  def readSensors(self):
    """ Returns a dictionary with the sensor values. """
    
    self._setMode(MODE_CAPTURE)
    while self._serial.inWaiting() > 300:
      self._serial.read(1)
    sensors = self._readResponse(300).split('\r\n')[1:]

    while sensors[0][0] != "a":
      sensors = sensors[1:]
      
    sensors = [ int(s[1:]) for s in sensors[0:12] ]
    return { "S1"     : not sensors[0],
             "S2"     : not sensors[1],
	     "S3"     :     sensors[2],
	     "S4"     :     sensors[3],
	     "S5"     : not sensors[4],
	     "S6"     : not sensors[5], 
	     "S7"     :     sensors[6],
	     "S8"     :     sensors[7],
	     "CPUBat" :     sensors[8],
	     "MOTBat" :     sensors[9],
	     "MOTERR" : not sensors[10],
	     "BtEnt"  : not sensors[11] }
  def setServoTable(self, servo, tabela):
    SERVO_ANGLE_TABLE[servo] = table

  def getServoApproximateAngle(self, servo, angle):
    angle = int(angle)
  
    if not SERVO_ANGLE_TABLE.haskey(id):
      raise AlfaException("InvalidServo")
    if SERVO_ANGLE_TABLE[id].haskey(angle):
      return SERVO_ANGLE_TABLE[id][angle]
    
    for a in sorted(SERVO_ANGLE_TABLE[id].keys()):
      if angle >= a:
        return a
    
    raise AlfaException("InvalidAngle")
    
  def moveServo(self, id, angle):
    angle = int(angle)
  
    if not SERVO_ANGLE_TABLE.haskey(id):
      raise AlfaException("InvalidServo")
    if not SERVO_ANGLE_TABLE[id].haskey(angle):
      raise AlfaException("InvalidAngle")
      
    self._setMode(MODE_CAPTURE)
    self._sendcommand("M%s" % SERVO[id])
    self._sendcommand("%d" % SERVO_ANGLE_TABLE[id][angle]) 

  def identify(self):
    """ Returns a dictionary with the robot identification (name, version and revision). """
  
    self._setMode(MODE_NORMAL)
    
    while self._serial.inWaiting() > 0:
      self._serial.read(1)
    
    self._sendCommand("Mn")
    response = self._readResponse(300).split("\r\n")
 
    while response[0][0] != 'r':
      response = response[1:]
      if response == []:
        return self.identify()	      
    
    return { "name"    : response[0][1:], 
             "version" : response[1][1:], 
	     "revision": response[2][1:] }
	     
  def motorSpeed(self, speed, motor = MOTOR_BOTH):
    """ Sets a given motor speed.
    
    Minimum speed is -10, maximum is 10. 0 the motor stops. Raises 
    AlfaException("InvalidSpeed") if speed is invalid. """
    
    if not (-10 <= speed <= 10):
      raise AlfaException("InvalidSpeed")
    
    if not (MOTOR_BOTH <= motor <= MOTOR_LEFT):
      raise AlfaException("InvalidMotor")
   
    speed += 11
    self._setMode(MODE_CAPTURE)

    if motor == MOTOR_BOTH or motor == MOTOR_LEFT:
      self._motor_left = speed - 11
      self._sendCommand("Me")
      self._sendCommand("%d" % speed)

    if motor == MOTOR_BOTH or motor == MOTOR_RIGHT:
      self._motor_right = speed - 11
      self._sendCommand("Md")
      self._sendCommand("%d" % speed)
  
  def motorForward(self, speed):
    self.motorSpeed(speed)

  def motorBackward(self, speed):
    self.motorForward(-speed)

  def motorLeft(self, speed):
    self.motorSpeed( speed,MOTOR_LEFT)
    self.motorSpeed(-speed,MOTOR_RIGHT)

  def motorRight(self, speed):
    self.motorSpeed(-speed,MOTOR_LEFT)
    self.motorSpeed( speed,MOTOR_RIGHT)

  def motorStop(self):
    self.motorSpeed(0)
  
  def sound(self, frequency, duration):
    self.soundStart(frequency)
    time.sleep(duration)
    self.soundStop()
  
  def soundStart(self, frequency):
    self._setMode(MODE_CAPTURE)
    self._sendCommand("MM")
    self._sendCommand("%d" % frequency)
    self._sound = True

  def soundStop(self):
    self._setMode(MODE_CAPTURE)
    self._sendCommand("Mm")
    self._sound = False
  
  def __del__(self):
    if self._sound:
      self.soundStop()
    if self._motor_left != 0 or self._motor_right != 0:
      self.motorSpeed(0)
    self._setMode(MODE_NORMAL)
    
    try:
      self._serial.close()
    except AttributeError:
      pass

if __name__ == '__main__':
  l = Alfa()
  print l.ping()
  print l.readSensors()
  print l.identify()
  l.motorSpeed(10)
  print "anda"
  time.sleep(2)
  l.motorSpeed(0)
  l.sound(50, 2)

  try:
    while 1: 
        a = l.readSensors()
        #print "\033[H\033[2J"
        #print a
        k = a.keys()
        k.sort()
        for i in k:
          print i, a[i]
  except KeyboardInterrupt :
    del(l)
    print "Bye" 
  except AlfaException:
    print AlfaException._cod

