import ConfigParser
import io

"""
board = 1 arduino
board = 2 raspberry
"""
default_config = """
[pi-home-automation]
board = arduino
"""

#import RPi.GPIO as GPIO
config = ConfigParser.RawConfigParser()
try:
	config.readfp(open('config.cfg'))
except IOError:
	print "File 'config.cfg' not exist. Load default configuration."
	config.readfp(io.BytesIO(default_config))

type_board = config.get('pi-home-automation', 'board')
print type_board
CH1=3
CH2=4
CH3=5
CH4=6
CH5=7
CH6=8
CH7=9
CH8=10
ALL_CH=(CH1,CH2,CH3,CH4,CH5,CH6,CH7,CH8)

if type_board == "arduino":
	from pyfirmata import Arduino, util
	try:
		board=Arduino('/dev/ttyACM0')
	except:
		print "Error initializing arduino."
		exit(1)
	for i in ALL_CH:
		board.digital[i].write(1)
	
elif type_board == "raspberry":
	try:
		import RPi.GPIO as GPIO
	except RuntimeError:
		print "This module can only be run on a Raspberry Pi!"
		exit(1)
	GPIO.setmode(GPIO.BOARD)
	CH1=11
	CH2=12
	CH3=13
	CH4=15
	CH5=16
	CH6=18
	CH7=22
	CH8=7
	GPIO.setup(ALL_CH, GPIO.OUT)
	GPIO.output(ALL_CH,GPIO.HIGH)

"""
"""
def board_write(CH, value):
	if type_board == "arduino":
		board.digital[CH].write(value)
	elif type_board == "raspberry":
		GPIO.output(CH, value)

def board_read(CH):
	if type_board == "arduino":
		return board.digital[CH].read()
	elif type_board == "raspberry":
		return GPIO.input(CH)
	return 0
