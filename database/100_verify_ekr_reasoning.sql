DO $$ BEGIN
 IF to_regclass('ekr_reasoning.reasoning_run') IS NULL THEN RAISE EXCEPTION 'Missing ekr_reasoning.reasoning_run'; END IF;
 IF to_regclass('ekr_reasoning.dependency_edge') IS NULL THEN RAISE EXCEPTION 'Missing ekr_reasoning.dependency_edge'; END IF;
 IF to_regclass('ekr_reasoning.impact_analysis') IS NULL THEN RAISE EXCEPTION 'Missing ekr_reasoning.impact_analysis'; END IF;
 IF to_regclass('ekr_reasoning.dependency_path') IS NULL THEN RAISE EXCEPTION 'Missing ekr_reasoning.dependency_path'; END IF;
 IF to_regclass('ekr_reasoning.root_cause_candidate') IS NULL THEN RAISE EXCEPTION 'Missing ekr_reasoning.root_cause_candidate'; END IF;
END $$;
