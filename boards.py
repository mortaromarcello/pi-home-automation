import ConfigParser
import io

"""
type =  arduino, raspberry
"""
default_config = """
[board]
type = arduino
"""
config = ConfigParser.RawConfigParser()

try:
	config.readfp(open('config.cfg'))
except IOError:
	print "File 'config.cfg' not exist. Load default configuration."
	config.readfp(io.BytesIO(default_config))


class Board:
	def __init__(self):
		self.type=""
		self.channels=8
		self.ALL_CH = {'CH1':1, 'CH2':2, 'CH3':3, 'CH4':4, 'CH5':5, 'CH6':6, 'CH7':7, 'CH8':8}
	def read(self, channel):
		pass
	
	def write(self, channel, value):
		pass

	def type(self):
		return self.type
	
class Arduino(Board):
	def __init__(self):
		Board.__init__(self)
		self.type="arduino"
		self.channels=8
		self.ALL_CH['CH1']=3
		self.ALL_CH['CH2']=4
		self.ALL_CH['CH3']=5
		self.ALL_CH['CH4']=6
		self.ALL_CH['CH5']=7
		self.ALL_CH['CH6']=8
		self.ALL_CH['CH7']=9
		self.ALL_CH['CH8']=10
		from pyfirmata import Arduino, util
		try:
			self.board=Arduino('/dev/ttyACM0')
		except:
			print "Error initializing arduino."
			exit(1)
		for i in self.ALL_CH.values():
			self.board.digital[i].write(1)
	
	def read(self, channel):
		return self.board.digital[channel].read()
	
	def write(self, channel, value):
		self.board.digital[channel].write(value)

class Raspberry(Board):
	def __init__(self):
		Board.__init__(self)
		self.type = "raspberry"
		self.channels = 8
		try:
			import RPi.GPIO as GPIO
		except RuntimeError:
			print "This module can only be run on a Raspberry Pi!"
			exit(1)
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
		return GPIO.input(channel)
	
	def write(self, channel, value):
		GPIO.output(channel, value)

type_board = config.get('board', 'type')
if type_board == "arduino":
	board = Arduino()
elif type_board == "raspberry":
	board = Raspberry()
	
if __name__ == "__main__":
	print board.ALL_CH
	for ch in board.ALL_CH.keys():
		print ch + "=" + str(board.read(board.ALL_CH[ch]))
