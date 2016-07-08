import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, nullable=True, autoincrement=True)
    name = Column(String(80), primary_key=True)
    email = Column(String(80), nullable=False)
    picture = Column(String(250), nullable=False)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'email': self.email,
            'picture': self.picture,
            'id': self.id,
        }


class Category(Base):
    __tablename__ = 'category'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'items': queryItems(self.id),
        }


def queryItems(id):
    items = session.query(Item).filter_by(category_id=id).all()

    # Create emmpty lists to store item names
    item_names = []

    for item in items:
        item_names.append(item.serialize)

    return item_names


class Item(Base):
    __tablename__ = 'item'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'user_id': self.user_id,
        }

engine = create_engine('sqlite:///itemcatalog.db')

Base.metadata.create_all(engine)
