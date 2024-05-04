from ProjectUtils.MessagingService.schemas import Service
from Wrappers.models import SessionLocal, property_id_mapper_by_service, reservation_id_mapper_by_service, \
    ReservationIdMapper, ReservationStatus, management_id_mapper_by_service


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
        print("external_property_id", external_property_id)
        print("property_record", property_record)
        print(property_record.internal_id if property_record is not None else property_record)
        return property_record.internal_id if property_record is not None else property_record


def set_property_internal_id(service: Service, external_property_id) -> int:
    with SessionLocal() as db:
        PropertyIdMapper = property_id_mapper_by_service[service]
        mapped_id = PropertyIdMapper(external_id=external_property_id)
        print("setting property internal id", service.value, external_property_id, mapped_id.internal_id)
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


def get_reservation_by_external_id(service: Service, external_reservation_id: int) -> ReservationIdMapper:
    with SessionLocal() as db:
        ReservationIdMapper = reservation_id_mapper_by_service[service]
        print("external_reservation_id", external_reservation_id)
        return db.query(ReservationIdMapper).filter(
            ReservationIdMapper.external_id == external_reservation_id).first()


def create_reservation(service: Service, external_reservation_id: int, reservation_status: str):
    with SessionLocal() as db:
        ReservationIdMapper = reservation_id_mapper_by_service[service]
        mapped_id = ReservationIdMapper(external_id=external_reservation_id,
                                        reservation_status=ReservationStatus(reservation_status))
        db.add(mapped_id)
        db.commit()
        db.refresh(mapped_id)
        return mapped_id


def update_reservation(service: Service, reservation_to_update_internal_id: int, reservation_status: str):
    with SessionLocal() as db:
        print(reservation_status)
        print(ReservationStatus(reservation_status))
        ReservationIdMapper = reservation_id_mapper_by_service[service]
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
        db.add(mapped_id_record)
        db.commit()
        db.refresh(mapped_id_record)
        return mapped_id_record
