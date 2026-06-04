from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
import os
import sys

# Python path configuration
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db, Base, engine
import models
import algorithm

# Database tables ko initial create karne ke liye
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/users/")
def create_user(name: str, phone: str, upi_id: str, db: Session = Depends(get_db)):
    db_user = models.User(name=name, phone=phone, upi_id=upi_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User created", "id": db_user.id}

@app.post("/groups/")
def create_group(name: str, member_ids: str, db: Session = Depends(get_db)):
    ids = json.loads(member_ids)
    db_group = models.Group(name=name)
    members = db.query(models.User).filter(models.User.id.in_(ids)).all()
    db_group.members = members
    db.add(db_group)
    db.commit()
    return {"message": "Group created", "id": db_group.id}

@app.post("/expenses/")
def add_expense(group_id: int, paid_by_id: int, amount: float, description: str, db: Session = Depends(get_db)):
    expense = models.Expense(group_id=group_id, paid_by_id=paid_by_id, amount=amount, description=description)
    db.add(expense)
    db.commit()
    db.refresh(expense)

    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    members_count = len(group.members)
    share = amount / members_count

    for member in group.members:
        split = models.ExpenseSplit(expense_id=expense.id, user_id=member.id, amount_owed=share)
        db.add(split)
    
    db.commit()
    return {"message": "Expense added and split equally!"}

@app.get("/groups/{group_id}/settle/")
def settle_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    txs = algorithm.simplify_debts(group.expenses, group.members)
    
    result = []
    for tx in txs:
        from_user = db.query(models.User).filter(models.User.id == tx["from_user_id"]).first()
        to_user = db.query(models.User).filter(models.User.id == tx["to_user_id"]).first()
        
        formatted_name = to_user.name.replace(' ', '%20')
        upi_link = f"upi://pay?pa={to_user.upi_id}&pn={formatted_name}&am={tx['amount']:.2f}&cu=INR&tn=Splitwise"
        
        result.append({
            "from": from_user.name,
            "to": to_user.name,
            "amount": tx["amount"],
            "upi_url": upi_link
        })
    return result

# 🔥 FORCED RESET: Yeh engine close karke completely tables ko clean aur rebuild karega
@app.post("/reset-database/")
def reset_database():
    try:
        engine.dispose()  # Connections close karo pehle
        Base.metadata.drop_all(bind=engine)  # Saare tables ko force-delete karo
        Base.metadata.create_all(bind=engine)  # Ekdum empty aur brand new schema banao
        return {"message": "Database completely wiped out and fresh tables created!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")
