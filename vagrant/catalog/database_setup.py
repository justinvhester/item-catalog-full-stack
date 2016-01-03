from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(50), nullable=False)
    picture = Column(String(250))


class Manufacturer(Base):
    __tablename__ = 'manufacturer'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    country = Column(String(50))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


class Disc(Base):
    __tablename__ = 'disc'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    disc_type = Column(String(16))
    description = Column(String(250))
    weight = Column(Integer(3))
    color = Column(String(250))
    picture = Column(String(250))
    condition = Column(String(250))
    manufacturer_id = Column(Integer, ForeignKey('manufacturer.id'))
    manufacturer = relationship(Manufacturer)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


engine = create_engine('sqlite:///discr.db')
Base.metadata.create_all(engine)
