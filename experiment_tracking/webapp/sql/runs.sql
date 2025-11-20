CREATE OR REPLACE FUNCTION to_paris_time(epoch_ms BIGINT)
RETURNS TEXT AS $$
BEGIN
    RETURN to_char(
        to_timestamp(epoch_ms / 1000)
        AT TIME ZONE 'UTC-1',
        'YYYY-MM-DD HH24:MI:SS'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

select
    r.user_id as "user",
    e.name as experiment_name,
    to_paris_time(e.creation_time) as experiment_creation,
    r.run_uuid as run_id,
    r.name as "name",
    r.status as "status",
    to_paris_time(r.start_time) as runtime_start,
    round((r.end_time - r.start_time)/1000::numeric, 2) as runtime_sec,
    r.deleted_time
from experiments e left join runs r on e.experiment_id = r.experiment_id
order by r.start_time