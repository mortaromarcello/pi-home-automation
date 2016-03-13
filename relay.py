# -*- coding: utf-8 -*-
from configuration import board_write as board_write
from configuration import board_read as board_read
from configuration import CH1 as CH1
from configuration import CH2 as CH2
from configuration import CH3 as CH3
from configuration import CH4 as CH4
from configuration import CH5 as CH5
from configuration import CH6 as CH6
from configuration import CH7 as CH7
from configuration import CH8 as CH8
from configuration import ALL_CH as ALL_CH

import argparse
import random
import os
import time
import datetime
import threading
import signal
import sys
import hashlib
import re
import cherrypy
import json
import urlparse
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage
from pyfirmata import Arduino, util
import models
from sqlalchemy.orm import sessionmaker,scoped_session
from mako.template import Template
from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=['html'])

engine = models.engine
session = models.session
users = models.User

class ChatWebSocketHandler(WebSocket):
	def received_message(self, m):
		global jsonLabels
		global board
		msg=m.data.decode("utf-8")
		try:
			jo=json.loads(msg)
		except(ValueError, KeyError, TypeError):
			cherrypy.log("Not Json");
		cmd=jo["c"]
		if (cmd=="update"):
			readJsonLabels()
			self.send(jsonLabels)
		elif(cmd=="on"):
			r=int(jo["r"])
			board_write(ALL_CH[r-1], 0)
			print "On:",r-1
		elif(cmd=="off"):
			r=int(jo["r"])
			board_write(ALL_CH[r-1], 1)
			print "Off:",r-1
		elif(cmd=="updateLabels"):
			readJsonLabels()
			d=json.loads(jsonLabels);
			d['relay'+str(jo['id'])]['label']=jo['newLabel']
			jsonLabels=json.dumps(d);
			saveJsonLabels(jsonLabels);
			cherrypy.engine.publish('websocket-broadcast', '%s ' %jsonLabels)
			print "Saved and Broadcasted";
		else:
			cherrypy.log("Not a command");
		#self.send(statusJSON(getStatus()))
		cherrypy.engine.publish('websocket-broadcast', statusJSON(getStatus()))

	def closed(self, code, reason="A client left the room without a proper explanation."):
		cherrypy.engine.publish('websocket-broadcast', TextMessage(reason))

class Root(object):
	def __init__(self, host, port, ssl=False):
		self.host = host
		self.port = port
		self.scheme = 'wss' if ssl else 'ws'
	
	@cherrypy.expose
	def index(self):
		urlP=urlparse.urlparse(cherrypy.request.base)
		self.create_db()
		tmpl = lookup.get_template("login.html")
		return tmpl.render()
	
	def doLogin(self, username=None, password=None):
		"""Check the username & password"""
		pwdhash = hashlib.md5(password).hexdigest()
		if username != "" and password != "":
			user = session.query(users).filter(users.name==username, users.password==pwdhash).first()
			if user != None:
				if user.name=="admin":
					tmpl = lookup.get_template("admin.html")
				else:
					tmpl = lookup.get_template("index.html")
				return tmpl.render()
		print "no user"
		tmpl = lookup.get_template("nouser.html")
		return tmpl.render()
	doLogin.exposed = True

	def doAdmin(self):
		tmpl = lookup.get_template("admin.html")
		return tmpl.render()
	doAdmin.exposed = True
	
	"""
	def doRegister(self):
		tmpl = lookup.get_template("register.html")
		return tmpl.render()
	doRegister.exposed = True
	"""
	
	def add(self, username, fname, password):
		pwdhash = hashlib.md5(password).hexdigest()
		try:
			user = session.query(users).filter(users.name==username).first()
			if user == None:
				new_user=users(name=username, fullname=fname, password=pwdhash)
				session.add(new_user)
				# invo la sessione e creo il nuovo utente in db
				session.commit()
		except:
			session.rollback()
			print "add("+username+","+pwdhash+")"
			tmpl = lookup.get_template("login.html")
			return tmpl.render()
		else:
			tmpl = lookup.get_template("nouser.html")
			return tmpl.render()
	add.exposed = True
	
	def create_db(self):
		# creo il db e tutte le tabelle nel database
		out = models.initialize_sql()
		admin_user=users("admin", "admin", "f28804c858110077f51dcaf3fd392fba")
		try:
			session.add(admin_user)
			session.commit()
		except:
			session.rollback()
		return "DB creato, Tabelle Create."
	
	@cherrypy.expose
	def ws(self):
		cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))

def getStatus():
	return [board_read(CH1),\
			board_read(CH2),\
			board_read(CH3),\
			board_read(CH4),\
			board_read(CH5),\
			board_read(CH6),\
			board_read(CH7),\
			board_read(CH8)]

def statusJSON(status):
	return '{"status":['+(', '.join(str(x) for x in status))+']}';

def stpoll(arg):
	global pollStatus, oldStatus, currentStatus
	while pollStatus:
		if 'WebSocket' in globals():
			currentStatus=getStatus()
			print currentStatus
			STATUS=statusJSON(currentStatus)
			if oldStatus!=currentStatus:
				cherrypy.engine.publish('websocket-broadcast', '%s ' %STATUS)
			oldStatus=currentStatus
		time.sleep(2)
	cherrypy.log("exiting thread");

def timing(arg):
	# read from json timing file and switch tho lights on / off based on the time of the day.
	global jsonLabels
	pollInterval=3;
	while pollStatus:
		currentDT=datetime.datetime.now()
		cT=time2sec(currentDT.hour, currentDT.minute, currentDT.second)
		data = json.loads(jsonLabels);
		dow=datetime.datetime.today().weekday()
		for o in data:
			id=data[o]['id']
			times=data[o]['times']
			for t in times:
				sTime=t['start']
				eTime=t['end']
				sT=time2sec(sTime[0],sTime[1],sTime[2])
				eT=time2sec(eTime[0],eTime[1],eTime[2])
				#print cT,sT,eT,cT-sT,cT-eT
				if (abs(cT-sT)<pollInterval):
					if ((1<<dow)&t['dow']!=0):
						board_write(ALL_CH[id-1], 0)
						cherrypy.engine.publish('websocket-broadcast', statusJSON(getStatus()))
				if (abs(cT-eT)<pollInterval):
					board_write(ALL_CH[id-1], 1)
					cherrypy.engine.publish('websocket-broadcast', statusJSON(getStatus()))
				
		time.sleep(pollInterval)
	return 0;

def signal_handler(signal, frame):
	# read from keyb for ctrl + c
	global pollStatus
	pollStatus=False
	cherrypy.engine.stop()
	cherrypy.engine.exit()
	cherrypy.log('You pressed Ctrl+C!')

def saveJsonLabels(jsTxt):
	fo=open('relayLabel.json','w')
	fo.write(jsTxt)
	fo.close()

def readJsonLabels():
	# Read 
	global jsonLabels
	fo=open('relayLabel.json')
	jsonLabels=fo.read()
	fo.close()

def time_in_range(start, end, x):
	"""Return true if x is in the range [start, end]"""
	if start <= end:
		return start <= x <= end
	else:
		return start <= x or x <= end

def time2sec(h,m,s):
	return s+(m*60)+(h*3600);

currentStatus=[1,1,1,1,1,1,1,1]
oldStatus=[0,0,0,0,0,0,0]
jsonLabels="{}"
readJsonLabels()

if __name__ == '__main__':
	import logging
	from ws4py import configure_logger
	print os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
	configure_logger(level=logging.DEBUG)
	signal.signal(signal.SIGINT, signal_handler)
	pollStatus=True 
	thread = threading.Thread(target = stpoll, args = (10, ))
	thread.daemon = True
	thread2 = threading.Thread(target = timing, args = (10, ))
	thread2.daemon = True
	thread2.start()
	thread.start()
	parser = argparse.ArgumentParser(description='Echo CherryPy Server')
	parser.add_argument('--host', default='0.0.0.0')
	parser.add_argument('-p', '--port', default=9000, type=int)
	parser.add_argument('--ssl', action='store_true')
	args = parser.parse_args()

	cherrypy.config.update({'server.socket_host': args.host,
							'server.socket_port': args.port,
							'tools.staticdir.root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))})

	if args.ssl:
		cherrypy.config.update({'server.ssl_certificate': './server.crt',
								'server.ssl_private_key': './server.key'})

	WebSocketPlugin(cherrypy.engine).subscribe()
	cherrypy.tools.websocket = WebSocketTool()
	pwd=os.getcwd();
	cherrypy.quickstart(Root(args.host, args.port, args.ssl), '', config={
			'/': {
				'tools.staticdir.on': True,
				'tools.staticdir.dir': ''
			},
			'/ws': {
				'tools.websocket.on': True,
				'tools.websocket.handler_cls': ChatWebSocketHandler
			},
			'/js': {
				'tools.staticdir.on': True,
				'tools.staticdir.dir': 'js'
			},
			'/fonts': {
				'tools.staticdir.on': True,
				'tools.staticdir.dir': 'fonts'
			}
  	});
	thread.join();
	#GPIO.cleanup();
