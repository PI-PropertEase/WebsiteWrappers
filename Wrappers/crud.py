import logging

from ProjectUtils.MessagingService.schemas import Service
from Wrappers.models import SessionLocal, property_id_mapper_by_service, reservation_id_mapper_by_service, \
    ReservationIdMapper, ReservationStatus, management_id_mapper_by_service

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def get_property_external_id(service: Service, internal_property_id: int) -> int:
    with SessionLocal() as db:
        PropertyIdMapper = property_id_mapper_by_service[service]
        property_record = db.query(PropertyIdMapper).get(internal_property_id)
        return property_record.external_id if property_record is not None else property_record


def get_property_internal_id(service: Service, external_property_id: int) -> int:
    with SessionLocal() as db:
        PropertyIdMapper = property_id_mapper_by_service[service]
        property_record = db.query(PropertyIdMapper).filter(
            PropertyIdMapper.external_id == external_property_id).first()
        LOGGER.info("Querying '%s' with external_property_id '%s'. Response: '%s'", PropertyIdMapper, external_property_id, property_record.__dict__)
        return property_record.internal_id if property_record is not None else property_record


def set_property_internal_id(service: Service, external_property_id) -> int:
    with SessionLocal() as db:
        PropertyIdMapper = property_id_mapper_by_service[service]
        mapped_id = PropertyIdMapper(external_id=external_property_id)
        LOGGER.info("Creating property in '%s' with external_property_id: '%s'", PropertyIdMapper, external_property_id)
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
            LOGGER.info("Deleting property with internal_id '%s' from '%s'", new_internal_id, IdMapperService)
            db.delete(property_to_update_or_delete)
        else:
            # update
            LOGGER.info("Updating property with old_internal_id '%s' to new_internal_id '%s' in %s since it's a duplicate.",
                        old_internal_id, new_internal_id, IdMapperService)
            property_to_update_or_delete.internal_id = new_internal_id
        db.commit()


def get_reservation_external_id(service: Service, internal_reservation_id: int) -> int:
    with SessionLocal() as db:
        ReservationIdMapper = reservation_id_mapper_by_service[service]
        reservation = db.query(ReservationIdMapper).get(internal_reservation_id)
        return reservation.external_id if reservation is not None else reservation


def get_reservation_by_external_id(service: Service, external_reservation_id: int) -> ReservationIdMapper:
    with SessionLocal() as db:
        ReservationIdMapper = reservation_id_mapper_by_service[service]
        return db.query(ReservationIdMapper).filter(
            ReservationIdMapper.external_id == external_reservation_id).first()


def create_reservation(service: Service, external_reservation_id: int, reservation_status: str):
    with SessionLocal() as db:
        ReservationIdMapper = reservation_id_mapper_by_service[service]
        LOGGER.info("Creating reservation in '%s' with external_id '%s' and status '%s'",
                    ReservationIdMapper, external_reservation_id, reservation_status)
        mapped_id = ReservationIdMapper(external_id=external_reservation_id,
                                        reservation_status=ReservationStatus(reservation_status))
        db.add(mapped_id)
        db.commit()
        db.refresh(mapped_id)
        return mapped_id


def update_reservation(service: Service, reservation_to_update_internal_id: int, reservation_status: str):
    with SessionLocal() as db:
        ReservationIdMapper = reservation_id_mapper_by_service[service]
        LOGGER.info("Updating reservation in '%s' with internal_id '%s'. NEW STATUS '%s'",
                    ReservationIdMapper, reservation_to_update_internal_id, reservation_status)
        reservation_to_update = db.query(ReservationIdMapper).get(reservation_to_update_internal_id)
        reservation_to_update.reservation_status = ReservationStatus(reservation_status)
        db.commit()
        db.refresh(reservation_to_update)
        return reservation_to_update


def get_management_event(service: Service, internal_management_event_id: int):
    with SessionLocal() as db:
        ManagementIdMapper = management_id_mapper_by_service[service]
        return db.query(ManagementIdMapper).get(internal_management_event_id)


def create_management_event(service: Service, management_event_internal_id: int, management_event_external_id: int):
    with SessionLocal() as db:
        ManagementIdMapper = management_id_mapper_by_service[service]
        mapped_id_record = ManagementIdMapper(
            internal_id=management_event_internal_id, external_id=management_event_external_id
        )
        LOGGER.info("Creating management event in '%s' with external_id '%s' and internal_id '%s'",
                    ManagementIdMapper, management_event_external_id, management_event_internal_id)
        db.add(mapped_id_record)
        db.commit()
        db.refresh(mapped_id_record)
        return mapped_id_record


def delete_management_event(service: Service, management_event_internal_id: int):
    with SessionLocal() as db:
        ManagementIdMapper = management_id_mapper_by_service[service]
        event_to_delete = db.query(ManagementIdMapper).get(management_event_internal_id)
        LOGGER.info("Deleting management event in '%s' with internal_id '%s'",
                    ManagementIdMapper, management_event_internal_id)
        db.delete(event_to_delete)
        db.commit()
