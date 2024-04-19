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


class SequenceId(Base):
    __tablename__ = "sequence_id"
    id = Column(Integer, primary_key=True)
    auto_incremented = Column(Integer)


class IdMapperZooking(Base):
    __tablename__ = "id_mapper_zooking"
    internal_id = Column(Integer, primary_key=True)
    external_id = Column(Integer)


class IdMapperClickAndGo(Base):
    __tablename__ = "id_mapper_clickandgo"
    internal_id = Column(Integer, primary_key=True)
    external_id = Column(Integer)


class IdMapperEarthStayin(Base):
    __tablename__ = "id_mapper_earthstayin"
    internal_id = Column(Integer, primary_key=True)
    external_id = Column(Integer)


table_by_service = {
    Service.ZOOKING: IdMapperZooking,
    Service.CLICKANDGO: IdMapperClickAndGo,
    Service.EARTHSTAYIN: IdMapperEarthStayin
}


@event.listens_for(SequenceId.__table__, 'after_create')
def insert_initial_id(target, connection, **kw):
    connection.execute(target.insert().values(auto_incremented=1))


@event.listens_for(IdMapperZooking, 'before_insert')
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

@event.listens_for(IdMapperClickAndGo, 'before_insert')
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

@event.listens_for(IdMapperEarthStayin, 'before_insert')
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


def get_property_mapped_id(service: Service, external_property_id):
    with SessionLocal() as db:
        IdMapperService = table_by_service[service]
        mapped_id = IdMapperService(external_id=external_property_id)
        db.add(mapped_id)
        db.commit()
        db.refresh(mapped_id)
        return mapped_id.internal_id


def set_property_mapped_id(service: Service, old_internal_id, new_internal_id):
    with SessionLocal() as db:
        IdMapperService = table_by_service[service]
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


Base.metadata.create_all(bind=engine)
