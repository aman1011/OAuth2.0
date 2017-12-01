# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship, sessionmaker
from passlib.apps import custom_app_context as pwd_context
import random, string
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)



Base = declarative_base()
class User(Base):
	__tablename__ = 'user'
	id = Column(Integer, primary_key = True)
	username = Column(String(32), index=True)
	picture = Column(String)
	email = Column(String)
	password_hash = Column(String(64))

	def hash_password(self, password):
		self.password_hash = pwd_context.encrypt(password)

	def verify_password(self, password):
		return pwd_context.verify(password, self.password_hash)

	def generate_auth_toke(self, expiration=600):
		s = Serializer(secret_key, expires_in = expiration)
		return s.dumps({'id': self.id})

	@staticmethod
	def verify_auth_token(token):
		s = Serializer(secret_key)
		try:
			data = s.loads(token)
		except SignatureExpired:

			# Valid Token, but expired
			return None
		except BadSignature:

			# Invalid Token
			return None
		user_id = data['id']
		return user_id

	@property
	def serialize(self):
		return {
			'id': self.id,
			'username': self.username,
			'picture': self.picture,
			'email': self.email,
			'password_hash': self.password_hash
		}


class Music_Band(Base):
	__tablename__ = 'music_band'
	id = Column(Integer, primary_key = True)
	name = Column(String(32), index=True)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
		return {
			'id': self.id,
			'name': self.name,
		}

class Album(Base):
	__tablename__ = 'album'
	id = Column(Integer, primary_key = True)
	name = Column(String(32), index=True)
	description = Column(String(400))
	music_band_id = Column(Integer, ForeignKey('music_band.id'))
	music_band = relationship(Music_Band)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
		return {
			'id': self.id,
			'name': self.name,
			'description': self.description,
		}


# Creating engine for the db file.
engine = create_engine('sqlite:///musicbandswithalbums.db')
Base.metadata.create_all(engine)


