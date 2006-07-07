#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Interface gr�fica para gerenciar o Kit Alfa da PNCA <http://www.pnca.com.br>
#
# Autor: Leandro Augusto Fogolin Pereira <leandro@linuxmag.com.br>
#

import gtk, gtk.glade, gobject
import threading
import alfa
import pyconsole
import sys

from math import ceil

class AlfaSensorThread(threading.Thread):
  """ This thread polls the sensors and executes commands either
  synchronized mode (immediateCommand) or in asynchronized mode
  (queueCommand). Synchronized commmands may return value, asynchronized
  ones do not return values.
  
  Whenever this thread is running, sensor data may be acquired by
  reading the 'sensors' attribute.  """
  
  def __init__(self):
    """ Initializes the sensor polling thread. May raise
    AlfaException("RobotNotResponding") if robot does
    not answer to a ping request. """
    
    threading.Thread.__init__(self)
    self.done = 0

    lock = threading.RLock()
    self.acquire = lock.acquire
    self.release = lock.release

    self._alfa = alfa.Alfa()
    if not self._alfa.ping():
      raise alfa.AlfaException("RobotNotResponding")
 
    self._cmdqueue = []
    self._lastcmd = None
    self.sensors = { "S1": 0, "S2": 0, "S3": 0, "S4": 0, "S5": 0,
                     "S6": 0, "S7": 0, "S8": 0, "CPUBat": 0,
		     "MOTBat": 0, "BtEnt": 0, "MOTERR": 0 }

  def queueCommand(self, cmdname, *args):
    """ Queues a command to be executed in the thread main loop.
    cmdname must be a valid method of Alfa."""
    
    self._cmdqueue.append((cmdname, args))

  def stop(self):
    """ Stops the thread and closes the connection. """
    self.done = True
    del(self._alfa)
    
  def immediateCommand(self, cmdname, *args):
    """ Executes a command immediately.
    cmdname must be a valid method of Alfa. """
    
    if not hasattr(self._alfa, cmdname):
      raise alfa.AlfaException("InvalidCommand")

    self._lastcmd = (cmdname, args)

    self.acquire()
    retval = getattr(self._alfa, cmdname)(*args)
    self.release()

    return retval

  def run(self):
    """ The thread main loop. Runs commands on queue and polls sensor data. """
    
    while not self.done:
      self.acquire()
      
      if self._cmdqueue:
      	cmdname, args = self._cmdqueue.pop(0)
        self.immediateCommand(cmdname, *args)
        
      try:
        self.sensors = self._alfa.readSensors()
      except:
        # The last command failed. Execute it again.
        if self._lastcmd:
	  cmdname, args = self._lastcmd
          self.immediateCommand(cmdname, *args)
	
      self.release()
	
class Widgets:
  """ Makes it easier to address a Glade window's widgets. Make
  every window this class' subclass, then access the widgets as
  if they were objects attributes.
  
  Optionally, you may access them as if your window were a dictionary
  of widgets. """
  
  def __init__(self, file):
    try:
      self.__widgets__ = gtk.glade.XML('glade/' + file)
      self.__widgetcache__ = {}
    except RuntimeError, msg:
      dialog = gtk.MessageDialog(type = gtk.MESSAGE_ERROR,
                                 buttons = gtk.BUTTONS_CLOSE)
      dialog.set_markup(_("Cannot find or load \"%s\".\n\n" \
                          "The system returned:\n%s") % (file, msg))
      dialog.run()
      dialog.destroy()
      
      gtk.main_quit()

  def __getitem__(self, key):
    if self.__widgetcache__.has_key(key):
      return self.__widgetcache__[key]
    else:
      self.__widgetcache__[key] = self.__widgets__.get_widget(key)
      return self.__widgetcache__[key]

  def __getattr__(self, key):
    try:
      return getattr(self, key)
    except:
      return self.__getitem__(key)
  
  def connectSignals(self, signal, widgets):
    """ Connects the widgets to the signal.
    
    Uses self.widget_nameSignalName as the signal handler. """
  
    # Converts "signal-name" to "SignalName"
    signalt = signal.replace("-", "_").title().replace("_", "")
    
    for widget in widgets:
      getattr(self, widget).connect(signal, getattr(self, '%s%s' % (widget, signalt)))

class MainWindow(Widgets):
  """ The main terminal window. """
  
  def _connect(self):
    try:
      self._alfa = AlfaSensorThread()
    except alfa.AlfaException:
      dialog = gtk.MessageDialog(type = gtk.MESSAGE_ERROR,
                                   buttons = gtk.BUTTONS_CLOSE)
      dialog.set_markup("<b><big>O robô não responde.</big></b>\n\n" \
                        "Favor verificar se:\n" \
                        " \342\200\242 O robô está conectado à serial\n" \
                        " \342\200\242 O robô está ligado\n" \
                        " \342\200\242 A luz amarela está acesa")
      dialog.run()
      dialog.destroy()

      self.btnConnect.set_active(False)
      return
      
    identity = self._alfa.immediateCommand('identify')
    self.lblName.set_text(identity["name"])
    self.lblVersion.set_text(identity["version"])
    self.lblRevision.set_text(identity["revision"])
 
    self.vbxControls.set_sensitive(True)

    self._alfa.start()
    self._connected = True
  
  def _disconnect(self):
    try:
      self._alfa.stop()
      self._connected = False
      self._alfa = None

      self.lblName.set_text("")
      self.lblVersion.set_text("")
      self.lblRevision.set_text("")
      
      self.vbxControls.set_sensitive(False)
    except:
      pass

  def btnConnectClicked(self, *args):
    if self.btnConnect.get_active():
      self._connect()
    else:
      self._disconnect()

  def btnMotorUpClicked(self, *args):
    if self.btnMotorUp.get_active():
      self._alfa.queueCommand('motorForward', ceil(self.sclMotorPower.get_value()))

  def btnMotorDownClicked(self, *args):
    if self.btnMotorDown.get_active():
      self._alfa.queueCommand('motorBackward', ceil(self.sclMotorPower.get_value()))

  def btnMotorLeftClicked(self, *args):
    if self.btnMotorLeft.get_active():
      self._alfa.queueCommand('motorLeft', ceil(self.sclMotorPower.get_value()))

  def btnMotorRightClicked(self, *args):
    if self.btnMotorRight.get_active():
      self._alfa.queueCommand('motorRight', ceil(self.sclMotorPower.get_value()))

  def btnMotorStopClicked(self, *args):
    if self.btnMotorStop.get_active():
      self._alfa.queueCommand('motorStop')

  def btnPlaySoundClicked(self, *args):
    if self.btnPlaySound.get_active():
      freq = self.sclSndFreq.get_value()
      self._alfa.queueCommand('soundStart', freq)
    else:
      self._alfa.queueCommand('soundStop')

  def btnQuitClicked(self, *args):
    if self._connected:
      self._disconnect()
    gtk.main_quit()
  
  def _updateSensors(self, *args):
    if self._connected and (self._alfa.sensors != self._sensors or self._sensorReadCount > 10):
      sensors = self._sensors = self._alfa.sensors
      self._sensorReadCount += 1
      if self._sensorReadCount > 10:
        self._sensorReadCount = 0

      self.sensorS1.set_active(sensors["S1"])
      self.sensorS2.set_active(sensors["S2"])
      self.sensorS5.set_active(sensors["S5"])
      self.sensorS6.set_active(sensors["S6"])
      self.sensorEnter.set_active(sensors["BtEnt"])

      self.sensorS3.set_fraction(sensors["S3"] / 1024.0)
      self.sensorS4.set_fraction(sensors["S4"] / 1024.0)
      self.sensorS7.set_fraction(sensors["S7"] / 1024.0)
      self.sensorS8.set_fraction(sensors["S8"] / 1024.0)

      self.batteryCPU.set_fraction(sensors["CPUBat"] / 1024.0)
      self.batteryMotor.set_fraction(sensors["MOTBat"] / 1024.0)
        
      while gtk.events_pending():
        gtk.main_iteration()
 
    return True
    
  def sclMotorPowerValueChanged(self, range, *args):
    if self._connected:
      if self.btnMotorUp.get_active():
        self.btnMotorUpClicked()
      elif self.btnMotorDown.get_active():
        self.btnMotorDownClicked()
      elif self.btnMotorLeft.get_active():
        self.btnMotorLeftClicked()
      elif self.btnMotorRight.get_active():
        self.btnMotorRightClicked()
    
  def sclSndFreqValueChanged(self, range, *args):
    if self._connected and self.btnPlaySound.get_active():
      self.btnPlaySoundClicked()

  def __init__(self):
    Widgets.__init__(self, "legalgtk.glade")

    self._connected = False
    self._alfa = None
    self._sensors = None
    self._sensorReadCount = 0

    widgets = [ 'btnConnect', 'btnMotorUp', 'btnMotorDown',
                'btnMotorLeft', 'btnMotorRight',
                'btnPlaySound', 'btnMotorStop', 'btnQuit' ]
    self.connectSignals('clicked', widgets)
    
    widgets = [ 'sclMotorPower', 'sclSndFreq' ]
    self.connectSignals('value-changed', widgets)

    self.wndMain.connect('delete-event', self.btnQuitClicked, None)
    gobject.timeout_add(5, self._updateSensors, self)

    self.cmbSerial.set_active(0)
    self.cmbSerial.set_sensitive(False)
    self.vbxControls.set_sensitive(False)
    
    swin = gtk.ScrolledWindow()
    swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
    swin.set_shadow_type(gtk.SHADOW_IN)
    console = pyconsole.Console(banner = "Use os metodos de 'alfa' para comunicar com o robo.",
                                use_rlcompleter = True,
                                locals = { "alfa" : self._alfa,
                                           "mainwindow" : self })
    swin.add(console)
    swin.show_all()

    self.frmConsole.add(swin)

    self.wndMain.show()

if __name__ == '__main__':
  mw = MainWindow()
  gtk.main()
