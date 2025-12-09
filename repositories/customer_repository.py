from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from models.customer import Customer
from schemas.customer import CustomerCreate, CustomerUpdate

class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def get_by_email(self, email: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.email == email).first()

    def create(self, customer: CustomerCreate) -> Customer:
        db_customer = Customer(
            full_name=customer.full_name,
            email=customer.email,
            phone=customer.phone,
            notes=customer.notes
        )
        self.db.add(db_customer)
        self.db.commit()
        self.db.refresh(db_customer)
        return db_customer

    def update(self, customer_id: UUID, customer_update: CustomerUpdate) -> Optional[Customer]:
        db_customer = self.get_by_id(customer_id)
        if not db_customer:
            return None

        update_data = customer_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_customer, key, value)

        self.db.commit()
        self.db.refresh(db_customer)
        return db_customer

    def delete(self, customer_id: UUID) -> bool:
        """Soft delete"""
        db_customer = self.get_by_id(customer_id)
        if not db_customer:
            return False

        db_customer.is_deleted = True
        db_customer.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def restore(self, customer_id: UUID) -> bool:
        """Restore soft deleted customer"""
        db_customer = self.get_by_id(customer_id)
        if not db_customer:
            return False

        db_customer.is_deleted = False
        db_customer.deleted_at = None
        self.db.commit()
        return True

    def list_customers(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        search_query: str = None, 
        include_deleted: bool = False
    ) -> Tuple[List[Customer], int]:
        query = self.db.query(Customer)

        if not include_deleted:
            query = query.filter(Customer.is_deleted == False)

        if search_query:
            search = f"%{search_query}%"
            query = query.filter(
                or_(
                    Customer.full_name.ilike(search),
                    Customer.email.ilike(search),
                    Customer.phone.ilike(search),
                    Customer.notes.ilike(search)
                )
            )

        total = query.count()
        customers = query.order_by(desc(Customer.created_at)).offset(skip).limit(limit).all()
        
        return customers, total
