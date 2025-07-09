from repositories.database import Base
from sqlalchemy import Column, Integer, String, Boolean


class Todos(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
    #owner_id = Column(Integer, ForeignKey("users.id"))


class MeasureData(Base):
    __tablename__ = 'MeasureData'

    id = Column(Integer, primary_key=True, index=True)
    deviceId = Column(String)
    speed = Column(String)
    rate = Column(String)
    total = Column(String)
    currentTime = Column(String)

class Aliases(Base):
    __tablename__ = 'Aliases'

    id = Column(Integer, primary_key=True, index=True)
    deviceId = Column(String)
    company = Column(String)
    location = Column(String)
    productName = Column(String)
    scaleId = Column(String)

class StaticParams(Base):
    __tablename__ = 'StaticParams'
    id = Column(Integer, primary_key=True, index=True)
    deviceId = Column(String)
    filterRate = Column(String)
    scaleCapacity = Column(String)
    autoZero = Column(String)
    deadBand = Column(String)
    scaleType = Column(String)
    loadcellSet = Column(String)
    loadcellCapacity = Column(String)
    trimm = Column(String)
    idlerSpacing = Column(String)
    speedSource = Column(String)
    wheelDiameter = Column(String)
    pulsesPerRev = Column(String)
    beltLength = Column(String)
    beltLengthPulses = Column(String)
    currentTime = Column(String)


