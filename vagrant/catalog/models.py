from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import random
import string


Base = declarative_base()


class Category(Base):
    __tablename__ = 'Category'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
        }


class Item(Base):
    __tablename__ = 'Item'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    category_id = Column(Integer, ForeignKey('Category.id'))
    category = relationship(Category, cascade="delete")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'cat_id': self.category_id,
            'description': self.description,
            'id': self.id,
            'title': self.name,
        }


engine = create_engine('sqlite:///catalog.db')


Base.metadata.create_all(engine)
