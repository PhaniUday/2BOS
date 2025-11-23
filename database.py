# --- IMPORTS ---
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- CODE BODY ---

# Define the location of the database file. 
# "sqlite:///./learning_platform.db" creates the file in the current folder.
SQLALCHEMY_DATABASE_URL = "sqlite:///./learning_platform.db"

# Create the engine that manages the connection.
# "check_same_thread": False is required specifically for SQLite logic in web servers.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a "Session" factory. 
# We use this to create temporary workspaces (sessions) to talk to the database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the Base class.
# All our database models (tables) will inherit from this class.
Base = declarative_base()