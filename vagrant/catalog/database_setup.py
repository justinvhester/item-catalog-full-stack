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

    @property
    def serialize(self):
        """Returns object data in an easy to serialize format"""
        return {
                'id' : self.id,
                'name' : self.name,
                'email' : self.email,
                'picture' : self.picture
                }


class Manufacturer(Base):
    __tablename__ = 'manufacturer'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    country = Column(String(50))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Returns object data in an easy to serialize format"""
        return {
                'id' : self.id,
                'name' : self.name,
                'country' : self.country,
                'user_name' : self.user.name
                }


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

    @property
    def serialize(self):
        """Returns object data in an easy to serialize format"""
        return {
                'id' : self.id,
                'name' : self.name,
                'disc_type': self.disc_type,
                'description': self.description,
                'weight': self.weight,
                'color': self.color,
                'picture': self.picture,
                'condition': self.condition,
                'manufacturer': self.manufacturer.name,
                'user': self.user.name
                }

engine = create_engine('sqlite:///discr.db')
Base.metadata.create_all(engine)
