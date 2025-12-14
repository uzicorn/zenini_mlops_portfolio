from .. import engine, ingestion_schema, logger
from datetime import datetime
import pandas
from pandas import errors
from sqlalchemy import text

class DataSet:
    def __init__(self, name: str, training_data: pandas.DataFrame, test_data: pandas.DataFrame):
        self.name = name
        self.training_data = training_data
        self.test_data = test_data

def create_dataset(name: str, raw_df: pandas.DataFrame, frac: float) -> DataSet:
    """
    Abstraction:
        dataset: A set of training and test data extracted from a raw dataframe
    Params: 
        raw_df: The raw data used for constructing the training and test datasets
        frac: the fraction of the dataset used for training
    Return : 
        A set used to construct an instance of DataSet
    """
    training_data=raw_df.sample(frac=frac, random_state=42, ignore_index=True)
    test_data=raw_df.drop(training_data.index).reset_index(drop=True)
    return DataSet(name, training_data, test_data)

def dataset_metadata(dataset: DataSet):
    """
    A dataset metadata is the actual table's schema.name in the postgres database 
    Example : mlops.iris_O.train , mlops.iris_O.test
    
    """
    return {
        'dataset_name': dataset.name,
        'training_data_tables': f'{dataset.name}_train',
        'test_data_tables' : f'{dataset.name}_test',
        'ingestion_date': datetime.now()
    }

def load_data(datasets: list[DataSet]):
    """
    datasets : A list of DataSet objects
    - Load the test and training data into the database
    - Load the metadata into {schema_name}.datasets_metadata
    """
    for dataset in datasets:
        metadata = dataset_metadata(dataset)       

        # Load training data    
        dataset.training_data.to_sql(
                                        con=engine, 
                                        schema=ingestion_schema, 
                                        name=metadata['training_data_tables'],
                                        index=False,
                                        if_exists='replace'
                                        )
        logger.info(f"Loaded {metadata['training_data_tables']} into schema {ingestion_schema}")
        
        # Load test data    
        dataset.test_data.to_sql(
                                con=engine, 
                                schema=ingestion_schema, 
                                name=metadata['test_data_tables'],
                                index=False,
                                if_exists='replace'
                                )
        logger.info(f"Loaded {metadata['test_data_tables']} into schema {ingestion_schema}")
        
        # Add a row in metadata table
        pandas.DataFrame(data=[metadata]).to_sql(
                        con=engine, 
                        schema=ingestion_schema, 
                        name="datasets_metadata",
                        if_exists='append'
                        )
        logger.info(f"Appended {dataset.name} metadata as a row in {ingestion_schema}.datasets_metadata")
        