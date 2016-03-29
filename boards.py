import ConfigParser
import io

FileConfig = 'config.cfg'

"""
type =  arduino, raspberry
"""
DefaultConfig = """
[board]
type = arduino
"""
Config = ConfigParser.RawConfigParser()

try:
	Config.readfp(open(FileConfig))
except IOError:
	print "File %s not exist. Load default configuration." % (FileConfig)
	Config.readfp(io.BytesIO(DefaultConfig))

class BoardError(Exception):
	def __init__(self, mismatch):
		Exception.__init__(self, mismatch)

class Board:
	def __init__(self):
		#global config
		self.type=""
		self.serial=""
		self.channels=8
		self.ALL_CH = {'CH1':1, 'CH2':2, 'CH3':3, 'CH4':4, 'CH5':5, 'CH6':6, 'CH7':7, 'CH8':8}
	def read(self, channel):
		pass
	
	def write(self, channel, value):
		pass

	def type(self):
		return self.type

	def serial(self):
		return self.serial
	
class Arduino(Board):
	def __init__(self):
		Board.__init__(self)
		self.serialPorts = ("/dev/ttyATM0","/dev/ttyATM1","/dev/ttyATM2","/dev/ttyUSB0","/dev/ttyUSB1","/dev/ttyUSB2")
		self.type = Config.get('board', 'type')
		if self.type != "arduino":
			print "Warning: type on file config not is arduino"
			self.type = "arduino"
		self.channels=8
		self.ALL_CH['CH1']=3
		self.ALL_CH['CH2']=4
		self.ALL_CH['CH3']=5
		self.ALL_CH['CH4']=6
		self.ALL_CH['CH5']=7
		self.ALL_CH['CH6']=8
		self.ALL_CH['CH7']=9
		self.ALL_CH['CH8']=10
		from pyfirmata import Arduino as arduino, util
		if self.setSerial() == True:
			self.board = arduino(self.serial)
		else:
			raise BoardError("Error initializing arduino.")
		for i in self.ALL_CH.values():
			self.board.digital[i].write(1)

	def setSerial(self):
		found = False
		from serial.serialutil import SerialException
		from pyfirmata import Arduino as arduino, util
		for s in self.serialPorts:
			try:
				arduino(s)
				found = True
			except (SerialException, OSError):
				found = False
				continue
			if found == True:
				self.serial = s
				return found
		return found
	
	def read(self, channel):
		return self.board.digital[channel].read()
	
	def write(self, channel, value):
		self.board.digital[channel].write(value)

class Raspberry(Board):
	def __init__(self):
		Board.__init__(self)
		self.type = Config.get('board', 'type')
		if self.type != "raspberry":
			print "Warning: type on file config not is raspberry"
			self.type = "raspberry"
		self.channels = 8
		try:
			import RPi.GPIO as GPIO
		except ImportError:
			raise BoardError("This module can only be run on a Raspberry Pi!")
		GPIO.setmode(GPIO.BOARD)
		self.ALL_CH['CH1']=11
		self.ALL_CH['CH2']=12
		self.ALL_CH['CH3']=13
		self.ALL_CH['CH4']=15
		self.ALL_CH['CH5']=16
		self.ALL_CH['CH6']=18
		self.ALL_CH['CH7']=22
		self.ALL_CH['CH8']=7
		GPIO.setup(ALL_CH, GPIO.OUT)
		GPIO.output(ALL_CH,GPIO.HIGH)
		
	def read(self, channel):
		try:
			return GPIO.input(channel)
		except NameError:
			raise BoardError("GPIO is not defined")
	
	def write(self, channel, value):
		try:
			GPIO.output(channel, value)
		except NameError:
			raise BoardError("GPIO is not defined")

def getBoard():
	typeBoard = Config.get('board', 'type')
	if typeBoard == "arduino":
		try:
			return Arduino()
		except:
			raise BoardError("Error initializing arduino")
	elif typeBoard == "raspberry":
		try:
			return Raspberry()
		except:
			raise BoardError("This module can only be run on a Raspberry Pi!")

if __name__ == "__main__":
	try:
		board = getBoard()
	except BoardError:
		print "Board Error!"
		board = None
	if board != None:
		print board.ALL_CH
		print board.serial
		for ch in board.ALL_CH.keys():
			print ch + "=" + str(board.read(board.ALL_CH[ch]))
