DO $$ BEGIN
 IF to_regclass('ekr_ai.enterprise_intelligence_run') IS NULL THEN RAISE EXCEPTION 'Missing ekr_ai.enterprise_intelligence_run'; END IF;
 IF to_regclass('ekr_ai.enterprise_finding') IS NULL THEN RAISE EXCEPTION 'Missing ekr_ai.enterprise_finding'; END IF;
 IF to_regclass('ekr_ai.enterprise_recommendation') IS NULL THEN RAISE EXCEPTION 'Missing ekr_ai.enterprise_recommendation'; END IF;
 IF to_regclass('ekr_ai.enterprise_question') IS NULL THEN RAISE EXCEPTION 'Missing ekr_ai.enterprise_question'; END IF;
 IF to_regclass('ekr_ai.enterprise_answer') IS NULL THEN RAISE EXCEPTION 'Missing ekr_ai.enterprise_answer'; END IF;
END $$;
