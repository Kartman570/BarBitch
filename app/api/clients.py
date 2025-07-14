from fastapi import APIRouter
from app.models.client import Client, ClientIn, ClientOut
from app.core.database import SessionDep
from sqlmodel import select
from fastapi import HTTPException, Query
from typing import Optional

router = APIRouter()


@router.post("/clients/", response_model=ClientOut)
def create_client(client_data: ClientIn, session: SessionDep) -> ClientOut:
    client = Client(**client_data.dict())
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


@router.get("/clients/", response_model=list[ClientOut])
def list_clients(
    session: SessionDep,
    name: Optional[str] = Query(None, description="Search clients by name"),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    offset: Optional[int] = Query(0, description="Offset for pagination")
) -> list[ClientOut]:
    query = select(Client)
    
    if name:
        query = query.where(Client.name.ilike(f"%{name}%"))
    
    if offset:
        query = query.offset(offset)
    
    if limit:
        query = query.limit(limit)
    
    clients = session.exec(query).all()
    return clients

@router.get("/clients/count")
def count_clients(session: SessionDep):
    query = select(Client)
    clients = session.exec(query).all()
    return {"count": len(clients)}

@router.get("/clients/{client_id}", response_model=ClientOut)
def get_client(client_id: int, session: SessionDep) -> ClientOut:
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


# @router.put("/clients/{client_id}", response_model=ClientOut)
# def update_client(client_id: int, client_data: ClientIn, session: SessionDep) -> ClientOut:
#     client = session.get(Client, client_id)
#     if client is None:
#         raise HTTPException(status_code=404, detail="Client not found")
    
#     for field, value in client_data.dict().items():
#         setattr(client, field, value)
    
#     session.add(client)
#     session.commit()
#     session.refresh(client)
#     return client


@router.patch("/clients/{client_id}", response_model=ClientOut)
def partial_update_client(client_id: int, client_data: ClientIn, session: SessionDep) -> ClientOut:
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    update_data = client_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


@router.delete("/clients/{client_id}")
def delete_client(client_id: int, session: SessionDep):
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    session.delete(client)
    session.commit()
    return {"message": "Client deleted successfully"}


@router.get("/clients/{client_id}/exists")
def check_client_exists(client_id: int, session: SessionDep):
    client = session.get(Client, client_id)
    return {"exists": client is not None}
