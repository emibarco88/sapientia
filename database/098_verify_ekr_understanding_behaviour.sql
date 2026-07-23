\set ON_ERROR_STOP on
SELECT to_regclass('ekr_understanding.business_process') AS business_process,
       to_regclass('ekr_understanding.process_step') AS process_step,
       to_regclass('ekr_understanding.process_transition') AS process_transition,
       to_regclass('ekr_understanding.process_evidence') AS process_evidence,
       to_regclass('ekr_understanding.snapshot_process') AS snapshot_process;
SELECT object_type_code, object_type_name FROM ekr_understanding.understanding_object_type WHERE object_type_code='PROCESS';
