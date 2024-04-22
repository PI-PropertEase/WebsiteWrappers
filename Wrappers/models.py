from sqlalchemy import Column, Integer, event, text
from sqlalchemy import create_engine
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


class SequenceIdProperties(Base):
    __tablename__ = "sequence_id_properties"
    id = Column(Integer, primary_key=True)
    auto_incremented = Column(Integer)


class SequenceIdReservations(Base):
    __tablename__ = "sequence_id_reservations"
    id = Column(Integer, primary_key=True)
    auto_incremented = Column(Integer)


class PropertyIdMapperZooking(Base):
    __tablename__ = "property_id_mapper_zooking"
    internal_id = Column(Integer, primary_key=True)
    external_id = Column(Integer)


class ReservationIdMapperZooking(Base):
    __tablename__ = "reservation_id_mapper_zooking"
    internal_id = Column(Integer, primary_key=True)
    external_id = Column(Integer)


class PropertyIdMapperClickAndGo(Base):
    __tablename__ = "property_id_mapper_clickandgo"
    internal_id = Column(Integer, primary_key=True)
    external_id = Column(Integer)


class ReservationIdMapperClickAndGo(Base):
    __tablename__ = "reservation_id_mapper_clickandgo"
    internal_id = Column(Integer, primary_key=True)
    external_id = Column(Integer)


class PropertyIdMapperEarthStayin(Base):
    __tablename__ = "property_id_mapper_earthstayin"
    internal_id = Column(Integer, primary_key=True)
    external_id = Column(Integer)


class ReservationIdMapperEarthStayin(Base):
    __tablename__ = "reservation_id_mapper_earthstayin"
    internal_id = Column(Integer, primary_key=True)
    external_id = Column(Integer)


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


@event.listens_for(SequenceIdProperties.__table__, 'after_create')
def insert_initial_id(target, connection, **kw):
    connection.execute(target.insert().values(auto_incremented=1))


@event.listens_for(SequenceIdReservations.__table__, 'after_create')
def insert_initial_id(target, connection, **kw):
    connection.execute(target.insert().values(auto_incremented=1))


@event.listens_for(PropertyIdMapperZooking, 'before_insert')
def increment_before_insert(mapper, connection, target):
    session = SessionLocal()
    try:
        with session.begin():
            global_counter = session.execute(text("SELECT auto_incremented FROM sequence_id")).scalar()
            target.internal_id = global_counter
            session.execute(text("UPDATE sequence_id SET auto_incremented = auto_incremented + 1"))
    except SQLAlchemyError as e:
        print(e)
        session.rollback()


@event.listens_for(PropertyIdMapperClickAndGo, 'before_insert')
def increment_before_insert(mapper, connection, target):
    session = SessionLocal()
    try:
        with session.begin():
            global_counter = session.execute(text("SELECT auto_incremented FROM sequence_id")).scalar()
            target.internal_id = global_counter
            session.execute(text("UPDATE sequence_id SET auto_incremented = auto_incremented + 1"))
    except SQLAlchemyError as e:
        print(e)
        session.rollback()


@event.listens_for(PropertyIdMapperEarthStayin, 'before_insert')
def increment_before_insert(mapper, connection, target):
    session = SessionLocal()
    try:
        with session.begin():
            global_counter = session.execute(text("SELECT auto_incremented FROM sequence_id")).scalar()
            target.internal_id = global_counter
            session.execute(text("UPDATE sequence_id SET auto_incremented = auto_incremented + 1"))
    except SQLAlchemyError as e:
        print(e)
        session.rollback()


@event.listens_for(ReservationIdMapperZooking, 'before_insert')
def increment_before_insert(mapper, connection, target):
    session = SessionLocal()
    try:
        with session.begin():
            global_counter = session.execute(text("SELECT auto_incremented FROM sequence_id")).scalar()
            target.internal_id = global_counter
            session.execute(text("UPDATE sequence_id SET auto_incremented = auto_incremented + 1"))
    except SQLAlchemyError as e:
        print(e)
        session.rollback()


@event.listens_for(ReservationIdMapperClickAndGo, 'before_insert')
def increment_before_insert(mapper, connection, target):
    session = SessionLocal()
    try:
        with session.begin():
            global_counter = session.execute(text("SELECT auto_incremented FROM sequence_id")).scalar()
            target.internal_id = global_counter
            session.execute(text("UPDATE sequence_id SET auto_incremented = auto_incremented + 1"))
    except SQLAlchemyError as e:
        print(e)
        session.rollback()


@event.listens_for(ReservationIdMapperEarthStayin, 'before_insert')
def increment_before_insert(mapper, connection, target):
    session = SessionLocal()
    try:
        with session.begin():
            global_counter = session.execute(text("SELECT auto_incremented FROM sequence_id")).scalar()
            target.internal_id = global_counter
            session.execute(text("UPDATE sequence_id SET auto_incremented = auto_incremented + 1"))
    except SQLAlchemyError as e:
        print(e)
        session.rollback()


def get_property_external_id(service: Service, internal_property_id: int) -> int:
    with SessionLocal() as db:
        PropertyIdMapper = property_id_mapper_by_service[service]
        return db.query(PropertyIdMapper).get(internal_property_id).external_id


def set_and_get_property_internal_id(service: Service, external_property_id):
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


def set_and_get_reservation_internal_id(service: Service, external_reservation_id):
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
