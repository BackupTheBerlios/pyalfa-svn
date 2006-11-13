#!/usr/bin/python
#
# Biblioteca para gerenciar o Kit Alfa da PNCA <http://www.pnca.com.br>
#
# Autores: Leandro Augusto Fogolin Pereira <leandro@linuxmag.com.br>
#          Fernando Paolieri Neto <fernando@cronuxs.net>
#

import serial
import time
import threading

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

SENSORS = {
	'a' : 'S1' ,
	'b' : 'S2' ,
	'c' : 'S3' ,
	'd' : 'S4' ,
	'e' : 'S5' ,
	'f' : 'S6' ,
	'g' : 'S7' ,
	'h' : 'S8' ,
	'i' : 'CPUBat',
	'j' : 'MOTBat',
	'k' : 'MOTERR',
	'l' : 'BtEnt' 
}

class AlfaException:
  def __init__(self, cod):
    self._cod = cod
  def __cmp__(self, cod):
    return self._cod == cod

class ReadSensors_Alfa(threading.Thread):
  def __init__ (self, serial):
    threading.Thread.__init__(self)
    self.serial  = serial
    self.alive   = True
    self.sensors = {}

    for i in 'abcdefghijkl':
      if i in 'abefkl': #Digital
        li = False
      else:
        li = 0
      self.sensors[SENSORS[i]] = li


  def read(self): 
    return self.sensors

  def run(self):
    while self.alive:
      sensors = self.serial.read(100)
      for i in sensors.split('\r\n'):
        try:
	  if i[0] in 'abefkl': #Digital
            li = not int(i[1:])
          else:
            li = int(i[1:])
          self.sensors[SENSORS[i[0]]] = li  
        except (ValueError,KeyError,IndexError):
          pass

class Alfa(object):
  def __init__(self, serial_port = 0, rate = 9600):
    """ Opens the connection with the robot. """
    
    self.DELAY = 0.035
    self._mode = MODE_NORMAL
    self._motor_right = 0
    self._motor_left = 0
    self._sound = False

    try:
      self._serial = serial.Serial(port = serial_port , baudrate=rate) 
      """ port = 0 => primeira porta serial disponivel """
      self._serial.timeout = 0.1
    except serial.serialutil.SerialException:
      raise AlfaException("SerialPortError")
    
    #self._thread = ReadSensors_Alfa(self._serial)
    
    if not self.ping():
      raise AlfaException("RobotNotResponding")

  def _setMode(self, mode):
    """ Sets the current operating mode. Raises AlfaException("InvalidMode") on invalid
    modes, does nothing if mode is current. """
    
    if self._mode == mode: return
    if self._motor_right != 0 or self._motor_left != 0: 
      raise AlfaException("MotorOnError")
    
    if self._sound:
      raise AlfaException("SoundOnError")
    
    if self._mode == MODE_CAPTURE:
      self._sendCommand("Mf")
      self._thread.alive = False;
      self._mode = MODE_NORMAL
      self._setMode(mode)
       
    elif self._mode == MODE_NORMAL:
      if mode == MODE_CAPTURE:
        self._thread = ReadSensors_Alfa(self._serial)
        self._thread.start() 
        self._sendCommand("Ms")
	self._mode = mode
    """
    da maneira que estava e possivel adcionar novos modos com facilidade! -- Fernando
	"""

  def _sendCommand(self, cmd):
    """ Sends a command to the robot. """
    print cmd
    self._serial.flushInput()
    self._serial.write("%s\r" % cmd)
    self._serial.flushOutput()
    time.sleep(self.DELAY)
  
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
    return self._thread.read()
  
  def setServoTable(self, servo, tabela):
    SERVO_ANGLE_TABLE[servo] = table

  def getServoApproximateAngle(self, servo, angle):
    angle = int(angle)
  
    if not SERVO_ANGLE_TABLE.has_key(servo):
      raise AlfaException("InvalidServo")
    if SERVO_ANGLE_TABLE[servo].has_key(angle):
      return SERVO_ANGLE_TABLE[servo][angle]
    
    for a in sorted(SERVO_ANGLE_TABLE[servo].keys()):
      if angle >= a:
        return a
    
    raise AlfaException("InvalidAngle")
    
  def moveServo(self, servo, angle):
    angle = int(angle)
  
    if not SERVO_ANGLE_TABLE.has_key(servo):
      raise AlfaException("InvalidServo")
    if not SERVO_ANGLE_TABLE[servo].has_key(angle):
      angle = self.getServoApproximateAngle(servo, angle)
      
    self._setMode(MODE_CAPTURE)
    self._sendCommand("M%s" % SERVO[servo])
    self._sendCommand("%d" % SERVO_ANGLE_TABLE[servo][angle]) 

  def identify(self):
    """ Returns a dictionary with the robot identification (name, version and revision). """
  
    self._setMode(MODE_NORMAL)
    
    while self._serial.inWaiting() > 0:
      self._serial.read(1)
    
    self._sendCommand("Mn")
    response = self._readResponse(300).split("\r\n")
 
    while response[0][0] != 'r':
      response = response[1:]
      if not response:
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
   
    self._setMode(MODE_CAPTURE)

    if motor == MOTOR_BOTH or motor == MOTOR_LEFT:
      self._motor_left = speed
      self._sendCommand("Me")
      self._sendCommand("%d" % (speed+11))

    if motor == MOTOR_BOTH or motor == MOTOR_RIGHT:
      self._motor_right = speed
      self._sendCommand("Md")
      self._sendCommand("%d" % (speed+11))
  
  def motorForward(self, speed):
    self.motorSpeed(speed)

  ## Metodos auxiliares para facilitar o uso da interface
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
  ## Fim dos metodos auxiliares
  
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
    self._thread.alive = False
    try:
      self._serial.close()
    except AttributeError:
      pass

if __name__ == '__main__':
  #l = Alfa( serial_port = "/dev/ttyUSB0", rate = 57600)
  l = Alfa( serial_port = "/dev/ttyUSB0")
  print "robo responde =>", l.ping()
  #print "sensores      =>", l.readSensors()
  #print "identificacao =>", l.identify()
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
  except AlfaException:
    print AlfaException._cod

