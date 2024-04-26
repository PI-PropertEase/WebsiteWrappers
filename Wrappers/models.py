from sqlalchemy import Column, Integer, event, text
from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ProjectUtils.MessagingService.schemas import Service

SQLALCHEMY_DATABASE_URL = "sqlite:///./idMapping.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Abstract Classes
class SequenceId(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    auto_incremented = Column(Integer)


class IdMapper(Base):
    __abstract__ = True
    internal_id = Column(Integer, primary_key=True)
    external_id = Column(Integer)


# Concrete Classes - SequenceId
class SequenceIdProperties(SequenceId): __tablename__ = "sequence_id_properties"


class SequenceIdReservations(SequenceId): __tablename__ = "sequence_id_reservations"


# Concrete Classes - PropertyIdMappers
class PropertyIdMapperZooking(IdMapper): __tablename__ = "property_id_mapper_zooking"


class PropertyIdMapperClickAndGo(IdMapper): __tablename__ = "property_id_mapper_clickandgo"


class PropertyIdMapperEarthStayin(IdMapper): __tablename__ = "property_id_mapper_earthstayin"


# Concrete Classes - ReservationIdMappers
class ReservationIdMapperZooking(IdMapper): __tablename__ = "reservation_id_mapper_zooking"


class ReservationIdMapperClickAndGo(IdMapper): __tablename__ = "reservation_id_mapper_clickandgo"


class ReservationIdMapperEarthStayin(IdMapper): __tablename__ = "reservation_id_mapper_earthstayin"


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
        print(e)
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
        print(e)
        session.rollback()


for ReservationIdMapper in reservation_id_mapper_by_service.values():
    listen(ReservationIdMapper, "before_insert", increment_reservation_sequence_id_before_insert)


# Helper functions
def get_property_external_id(service: Service, internal_property_id: int) -> int:
    with SessionLocal() as db:
        PropertyIdMapper = property_id_mapper_by_service[service]
        property = db.query(PropertyIdMapper).get(internal_property_id)
        return property.external_id if property is not None else property


def set_or_get_property_internal_id(service: Service, external_property_id: int) -> int:
    with SessionLocal() as db:
        PropertyIdMapper = property_id_mapper_by_service[service]
        property_record = db.query(PropertyIdMapper).filter(
            PropertyIdMapper.external_id == external_property_id).first()
        if property_record is not None:
            return property_record.internal_id
        mapped_id = PropertyIdMapper(external_id=external_property_id)
        db.add(mapped_id)
        db.commit()
        db.refresh(mapped_id)
        return mapped_id.internal_id


def set_property_internal_id(service: Service, external_property_id) -> int:
    with SessionLocal() as db:
        PropertyIdMapper = property_id_mapper_by_service[service]
        mapped_id = PropertyIdMapper(external_id=external_property_id)
        db.add(mapped_id)
        db.commit()
        db.refresh(mapped_id)
        return mapped_id.internal_id


def set_property_mapped_id(service: Service, old_internal_id, new_internal_id):
    with SessionLocal() as db:
        IdMapperService = property_id_mapper_by_service[service]
        property_with_same_internal_id = db.query(IdMapperService).get(new_internal_id)
        property_to_update_or_delete = db.query(IdMapperService).get(old_internal_id)
        if property_with_same_internal_id is not None:
            # delete
            print(f"\nold_internal_id: {old_internal_id}, new_internal_id: {new_internal_id}")
            print("property_with_same_internal_id: ", property_with_same_internal_id.__dict__)
            print("property_to_delete", property_to_update_or_delete.__dict__)
            db.delete(property_to_update_or_delete)
        else:
            # update
            print(f"\nold_internal_id: {old_internal_id}, new_internal_id: {new_internal_id}")
            print("property_to_update", property_to_update_or_delete.__dict__)
            property_to_update_or_delete.internal_id = new_internal_id
        db.commit()


def get_reservation_external_id(service: Service, internal_reservation_id: int) -> int:
    with SessionLocal() as db:
        ReservationIdMapper = reservation_id_mapper_by_service[service]
        reservation = db.query(ReservationIdMapper).get(internal_reservation_id)
        return reservation.external_id if reservation is not None else reservation


def get_reservation_internal_id(service: Service, external_reservation_id: int) -> int:
    with SessionLocal() as db:
        ReservationIdMapper = reservation_id_mapper_by_service[service]
        print("external_reservation_id", external_reservation_id)
        reservation = db.query(ReservationIdMapper).filter(ReservationIdMapper.external_id == external_reservation_id).first()
        return reservation.internal_id if reservation is not None else reservation


def set_and_get_reservation_internal_id(service: Service, external_reservation_id):
    with SessionLocal() as db:
        ReservationIdMapper = reservation_id_mapper_by_service[service]
        mapped_id = ReservationIdMapper(external_id=external_reservation_id)
        db.add(mapped_id)
        db.commit()
        db.refresh(mapped_id)
        return mapped_id.internal_id


def set_reservation_internal_id(service: Service, external_reservation_id):
    with SessionLocal() as db:
        ReservationIdMapper = reservation_id_mapper_by_service[service]
        mapped_id = ReservationIdMapper(external_id=external_reservation_id)
        db.add(mapped_id)
        db.commit()
        db.refresh(mapped_id)
        return mapped_id.internal_id


def set_reservation_mapped_id(service: Service, old_internal_id, new_internal_id):
    with SessionLocal() as db:
        ReservationIdMapper = reservation_id_mapper_by_service[service]
        reservation_with_same_internal_id = db.query(ReservationIdMapper).get(new_internal_id)
        reservation_to_update_or_delete = db.query(ReservationIdMapper).get(old_internal_id)
        if reservation_with_same_internal_id is not None:
            # delete
            print(f"\nold_internal_id: {old_internal_id}, new_internal_id: {new_internal_id}")
            print("reservation_with_same_internal_id: ", reservation_with_same_internal_id.__dict__)
            print("reservation_to_delete", reservation_to_update_or_delete.__dict__)
            db.delete(reservation_to_update_or_delete)
        else:
            # update
            print(f"\nold_internal_id: {old_internal_id}, new_internal_id: {new_internal_id}")
            print("reservation_to_update", reservation_to_update_or_delete.__dict__)
            reservation_to_update_or_delete.internal_id = new_internal_id
        db.commit()


Base.metadata.create_all(bind=engine)
