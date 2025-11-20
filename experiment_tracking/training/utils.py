from datetime import datetime
import os
import logging

from sklearn.linear_model import LogisticRegression
from mlflow.models.signature import infer_signature
from mlflow.data.pandas_dataset import from_pandas
from sklearn.metrics import accuracy_score
from pandas import DataFrame
import mlflow.sklearn

from .. import ingestion_schema, logger

def mlflow_configuration():
    """
    - Set log level to warning
    - Define server URI
    - Set experiment name
    """
    logging.getLogger("mlflow").setLevel(logging.WARNING)

    ec2_public_url = os.getenv('EC2_PUBLIC_URL')
    mlflow.set_tracking_uri(f'http://{ec2_public_url}:5000')

    experiment_name = "mlops_portfolio"
    try:
        experiment_id = mlflow.create_experiment(experiment_name)
    except mlflow.exceptions.MlflowException:
        logger.warning(f"Experiment {experiment_name} already exists.")
        experiment_id = mlflow.get_experiment_by_name(experiment_name).experiment_id
    mlflow.set_experiment(experiment_id=experiment_id)  
    experiment = mlflow.get_experiment(experiment_id=experiment_id)
    
    logger.info({'mlflow config':[{'Log level': 'Info', 'Server Url': mlflow.get_tracking_uri(),'Experiment': experiment.name,"Artifact_uri": experiment.artifact_location}]})

def check_no_active_run():
    if mlflow.active_run() is not None:
        logger.warning(f'There is an active run before the training : {mlflow.active_run()}')
        exit()

def log_dataframe(df, context):
    """
    
    """
    # MLFLOW wants an URL as a DataFrame source. I have a custom Postgres table
    # therefore the source is None. I put the table location in the context
    mlflow.log_input(
        dataset=from_pandas(df, source=None), 
        context=context
    )
    
def get_model_signature(sample, model: LogisticRegression):
    return infer_signature(model_input=sample, model_output=model.predict(sample))

def classification_training(model_name, train_df: DataFrame, test_df: DataFrame, param_dict, target_column):
    # Split th dataset
    X_train = train_df.drop(columns=[target_column])
    y_train = train_df[target_column]
    X_test  = test_df.drop(columns=[target_column])
    y_test  = test_df[target_column]
    
    # Start run
    check_no_active_run()

    """
        What follows is irrelevent to the portfolio as it is not part of
        the job I am applying to (MLOps) but rather to the Data Scientist.
    """ 
    with mlflow.start_run(run_name=f"run_{model_name}"):
        # Register the datasets at the experiment level
        log_dataframe(df=train_df, context=f"{ingestion_schema}.{train_df.name}")
        log_dataframe(df=test_df , context=f"{ingestion_schema}.{test_df.name}")
        
        # Train model
        logger.info(f"======= Training {model_name} =======")
        model = LogisticRegression(**param_dict, max_iter=200, random_state=42)
        model.fit(X_train, y_train)
        logger.info(f"End of training")
        # Predict and evaluate
        logger.info(f"Evaluating {model_name}")
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        logger.info(f"Measured accuracy: {acc}")
        
        # Log params and metrics
        for k,v in param_dict.items():
            mlflow.log_param(k, v)
        mlflow.log_metric("accuracy", acc)
        logger.info(f"Logged training parameters: {param_dict} ")
        
        """
            End of irrelevency, back to MlOps 
        """ 
        # Log the model if accuracy > 0.8
        if acc > 0.8:
            logger.info(f"Saving model artifact for {model_name} car accuracy > 80%")
            signature = get_model_signature(model=model, sample=X_test.iloc[:5])
            mlflow.sklearn.log_model(
                sk_model=model, 
                artifact_path=f"{model_name}",
                signature=signature)
            mlflow.log_param(key='artifact_saved', value='True')
        else : 
            mlflow.log_param(key='artifact_saved', value='False')

        logger.info(f"== End of process for {model_name} ==")
