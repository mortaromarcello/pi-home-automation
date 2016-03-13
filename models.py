from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String

engine = create_engine('sqlite:///mydatabase.db', connect_args={'check_same_thread':False}, echo=True)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# creo il metadata dalla base
metadata = Base.metadata

# creo la sessione al database
Session = sessionmaker(bind=engine)
session = Session()

class User(Base):
	__tablename__ = 'users'

	id = Column(Integer, primary_key=True)
	name = Column(String)
	fullname = Column(String)
	password = Column(String)

	def __init__(self, name, fullname, password):
		self.name = name
		self.fullname = fullname
		self.password = password

	def __repr__(self):
	   return "<User('%s','%s', '%s')>" % (self.name, self.fullname, self.password)


users_table = User.__table__
metadata = Base.metadata

def initialize_sql():
	# crea le tabelle all'interno del database
	metadata.create_all(engine)
