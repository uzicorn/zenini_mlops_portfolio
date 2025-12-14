import pandas
from dotenv import load_dotenv
import mlflow

from .utils import classification_training, mlflow_configuration, check_no_active_run
from .. import engine, ingestion_schema, logger

load_dotenv()


if __name__ == '__main__':
    logger.info(f"=============== RUNNING IRIS CLASSIFICATION TRAINING ===================")

    logger.info('Loading datasets from database')

    with engine.connect() as con:
        iris_0_train = pandas.read_sql_table(con=con, schema=ingestion_schema ,table_name='iris_0_train')
        iris_0_train.name = "iris_0_train"
        iris_0_test  = pandas.read_sql_table(con=con, schema=ingestion_schema ,table_name='iris_0_test')
        iris_0_test.name = "iris_0_test"
        iris_1_train = pandas.read_sql_table(con=con, schema=ingestion_schema ,table_name='iris_1_train')
        iris_1_train.name = "iris_1_train"
        iris_1_test  = pandas.read_sql_table(con=con, schema=ingestion_schema ,table_name='iris_1_test')
        iris_1_test.name = "iris_1_test"

    logger.info('Loaded iris_0_[train, test], iris_1_[train, test]')

    # MLflow setup
    mlflow_configuration()

    #--------------
    # TRAIN MODELS |
    #--------------
    param_dict={"C":1.0, "solver":"lbfgs"}
    classification_training(
    model_name   ="model_classification_1", 
    train_df     = iris_0_train, 
    test_df      = iris_0_test, 
    param_dict   = param_dict,
    target_column= 'target')
    #----------------------------------------------------------------------
    param_dict={"C":0.1, "solver":"lbfgs"}
    classification_training(
    model_name   ="model_classification_2", 
    train_df     = iris_0_train, 
    test_df      = iris_0_test, 
    param_dict   = param_dict,
    target_column= 'target')
    #----------------------------------------------------------------------
    param_dict={"C":0.1, "solver":"lbfgs"}
    classification_training(
    model_name   ="model_classification_3", 
    train_df     = iris_1_train, 
    test_df      = iris_1_test, 
    param_dict   = param_dict,
    target_column= 'target')
    #----------------------------------------------------------------------
    logger.info(f"=============== ENDING IRIS CLASSIFICATION TRAINING ====================")