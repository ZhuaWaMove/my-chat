from app.db.session import engine, Base
from app.models.chat import Session, Message

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")
