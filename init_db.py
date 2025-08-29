from app import app, db
import os

# create a new database within the app context
with app.app_context():
    db.create_all()
    print("Database created successfully")
