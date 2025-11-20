SELECT
    name as run_name,
    artifact_uri
FROM runs r
ORDER BY r.start_time asc
