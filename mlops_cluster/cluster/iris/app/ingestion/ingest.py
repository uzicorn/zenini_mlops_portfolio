from .utils import load_data
from .iris_connector import get_iris
from .. import engine, ingestion_schema, logger

if __name__ == '__main__':
    logger.info(f"=============== RUNNING INGESTION ===================")

    with engine.connect() as con:
        try:
            logger.info("Loading IRIS data into database")
            load_data(datasets=get_iris())
            logger.info(f"Loaded all IRIS tables into database schema {ingestion_schema}")
        except Exception as e:
            logger.warning("Couldn't load iris datasets into into database schema {ingestion_schema}")
            raise e

    logger.info(f"=============== ENDING INGESTION ====================")
