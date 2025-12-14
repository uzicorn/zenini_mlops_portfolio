from sklearn.datasets import load_iris
from pandas import DataFrame
from .utils import DataSet, create_dataset

def get_iris()-> list[DataSet]:
    """
    Ingest raw iris training data
    Returns a list of dataset objects
    1 dataset = Training and test data
    """
    data = []
    # Iris Dataset
    # Load raw data
    raw_iris = load_iris(as_frame=True)
    df_iris = DataFrame(raw_iris['data'].join(raw_iris['target']))
    # Clean raw data
    df_iris.rename(
        columns={
            "sepal length (cm)": "sepal_length_cm", 
            "sepal width (cm)": "sepal_width_cm",
            "petal length (cm)": "petal_length_cm",
            "petal width (cm)": "petal_width_cm"
            }, 
        inplace=True
        )
    # Convert int to float so that MlFlow don't harass me
    int_cols = df_iris.select_dtypes(include="int").columns
    df_iris[int_cols] = df_iris[int_cols].astype("float64")

    # Create datasets
    data.append(
        create_dataset(name='iris_0', raw_df=df_iris, frac=0.8)
        )
    data.append(
        create_dataset(name='iris_1', raw_df=df_iris, frac=0.75)
        )
    return data

