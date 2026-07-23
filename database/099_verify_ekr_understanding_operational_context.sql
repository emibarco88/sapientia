\set ON_ERROR_STOP on
SELECT to_regclass('ekr_understanding.object_context') AS object_context,
       to_regclass('ekr_understanding.object_context_fact') AS object_context_fact;
SELECT COUNT(*) AS object_context_count FROM ekr_understanding.object_context;
