from fastapi import HTTPException
from sqlalchemy import select


class Repository:
    def __init__(self, session, model):
        self.session = session
        self.model = model

    def get(self, identifier):
        item = self.session.get(self.model, identifier)
        if item is None:
            raise HTTPException(404, "Resource not found")
        return item

    def list(self, **filters):
        return self.session.scalars(select(self.model).filter_by(**filters)).all()

    def create(self, **values):
        item = self.model(**values)
        self.session.add(item)
        self.session.commit()
        return item
