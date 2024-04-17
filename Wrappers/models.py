from sqlalchemy import Column, Integer, ForeignKey, event, text
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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




def get_property_mapped_id(external_property_id):
    with SessionLocal() as db:
        mapped_id_zooking = IdMapperZooking(external_id=external_property_id)
        db.add(mapped_id_zooking)
        db.commit()
        db.refresh(mapped_id_zooking)
        return mapped_id_zooking.internal_id


Base.metadata.create_all(bind=engine)
