import logging

from sqlalchemy import Column, Integer, event, text, Enum
from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from enum import Enum as EnumType

from ProjectUtils.MessagingService.schemas import Service

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

SQLALCHEMY_DATABASE_URL = "sqlite:///./idMapping.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Enums
class ReservationStatus(EnumType):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELED = "canceled"


# Abstract Classes
class SequenceId(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    auto_incremented = Column(Integer)


class IdMapper(Base):
    __abstract__ = True
    internal_id = Column(Integer, primary_key=True)
    external_id = Column(Integer)


class PropertyIdMapper(IdMapper): __abstract__ = True


class ReservationIdMapper(IdMapper):
    __abstract__ = True
    reservation_status = Column(Enum(ReservationStatus))


class ManagementIdMapper(IdMapper): __abstract__ = True


# Concrete Classes - SequenceId
class SequenceIdProperties(SequenceId): __tablename__ = "sequence_id_properties"


class SequenceIdReservations(SequenceId): __tablename__ = "sequence_id_reservations"


# Concrete Classes - PropertyIdMappers
class PropertyIdMapperZooking(PropertyIdMapper): __tablename__ = "property_id_mapper_zooking"


class PropertyIdMapperClickAndGo(PropertyIdMapper): __tablename__ = "property_id_mapper_clickandgo"


class PropertyIdMapperEarthStayin(PropertyIdMapper): __tablename__ = "property_id_mapper_earthstayin"


# Concrete Classes - ReservationIdMappers
class ReservationIdMapperZooking(ReservationIdMapper): __tablename__ = "reservation_id_mapper_zooking"


class ReservationIdMapperClickAndGo(ReservationIdMapper): __tablename__ = "reservation_id_mapper_clickandgo"


class ReservationIdMapperEarthStayin(ReservationIdMapper): __tablename__ = "reservation_id_mapper_earthstayin"


# Concrete Classes - ManagementEventIdMappers
class ManagementIdMapperZooking(ManagementIdMapper): __tablename__ = "management_id_mapper_zooking"


class ManagementIdMapperClickAndGo(ManagementIdMapper): __tablename__ = "management_id_mapper_clickandgo"


class ManagementIdMapperEarthStayin(ManagementIdMapper): __tablename__ = "management_id_mapper_earthstayin"


# Mappers (service -> corresponding Property or Reservation IdMapper)
property_id_mapper_by_service = {
    Service.ZOOKING: PropertyIdMapperZooking,
    Service.CLICKANDGO: PropertyIdMapperClickAndGo,
    Service.EARTHSTAYIN: PropertyIdMapperEarthStayin
}

reservation_id_mapper_by_service = {
    Service.ZOOKING: ReservationIdMapperZooking,
    Service.CLICKANDGO: ReservationIdMapperClickAndGo,
    Service.EARTHSTAYIN: ReservationIdMapperEarthStayin
}

management_id_mapper_by_service = {
    Service.ZOOKING: ManagementIdMapperZooking,
    Service.CLICKANDGO: ManagementIdMapperClickAndGo,
    Service.EARTHSTAYIN: ManagementIdMapperEarthStayin
}


# Triggers
@event.listens_for(SequenceIdProperties.__table__, 'after_create')
@event.listens_for(SequenceIdReservations.__table__, 'after_create')
def insert_initial_id(target, connection, **kw):
    connection.execute(target.insert().values(auto_incremented=1))


def increment_property_sequence_id_before_insert(mapper, connection, target):
    session = SessionLocal()
    try:
        with session.begin():
            global_counter = session.execute(text("SELECT auto_incremented FROM sequence_id_properties")).scalar()
            target.internal_id = global_counter
            session.execute(text("UPDATE sequence_id_properties SET auto_incremented = auto_incremented + 1"))
    except SQLAlchemyError as e:
        LOGGER.error("Error while incrementing auto_incremented sequence_id for PROPERTIES: '%s'", e._message)
        session.rollback()


for PropertyIdMapper in property_id_mapper_by_service.values():
    listen(PropertyIdMapper, "before_insert", increment_property_sequence_id_before_insert)


def increment_reservation_sequence_id_before_insert(mapper, connection, target):
    session = SessionLocal()
    try:
        with session.begin():
            global_counter = session.execute(text("SELECT auto_incremented FROM sequence_id_reservations")).scalar()
            target.internal_id = global_counter
            session.execute(text("UPDATE sequence_id_reservations SET auto_incremented = auto_incremented + 1"))
    except SQLAlchemyError as e:
        LOGGER.error("Error while incrementing auto_incremented sequence_id for RESERVATIONS: '%s'", e._message)
        session.rollback()


for ReservationIdMapper in reservation_id_mapper_by_service.values():
    listen(ReservationIdMapper, "before_insert", increment_reservation_sequence_id_before_insert)

Base.metadata.create_all(bind=engine)
