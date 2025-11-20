select  
    d.dataset_source::json #> '{tags, mlflow.user}' as user,
    e.name as experiment_name,
    r.name as run_name,
    it.value as postgres_table_name,
    d.dataset_profile::json -> 'num_rows' as row_number,
    regexp_replace(d.dataset_source::json #>> '{tags, mlflow.source.name}', '.*/', '') as script_path
from input_tags it
inner join inputs i on i.input_uuid = it.input_uuid
inner join datasets d on i.source_id = d.dataset_uuid
inner join runs r on i.destination_id = r.run_uuid
inner join experiments e on r.experiment_id = e.experiment_id
where i.destination_type = 'RUN';