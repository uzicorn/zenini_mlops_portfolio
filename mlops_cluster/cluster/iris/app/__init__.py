from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from pathlib import Path
import os
import logging

logging.getLogger("mlflow").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

"""
- "schema_name" : Postgres schema where the ingested data is stored
- "engine"      : Sqlalchemy connexion engine to the RDS initiated once per module call
"""

# .env lives inside the module, its path has to be resolved
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

# Create Engine once mer module call.
user = os.getenv("user")
password = os.getenv("password")
host = os.getenv("host")
port = os.getenv("port")
dbname = os.getenv("dbname")
constring = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

engine = create_engine(constring)

# ML data location in RDS
ingestion_schema = os.getenv('RDS_INGESTION_SCHEMA') # The Postgres Schema where all the training and testing data lives

# Check for SQL ingestion
if any(suspicious in ingestion_schema.lower() for suspicious in ['drop', ';', 'create', 'admin', 'concat']):
    raise ValueError("The schema name may contains SQL injection !")

# Create ingestion schema in RDS if it doesn't exist
logger.info(f"Creting schema {ingestion_schema} if not exit.")
with engine.connect() as con:
    con.execute(text(f"CREATE SCHEMA IF NOT EXISTS {ingestion_schema};"))
    con.commit()