CREATE TABLE ekr_business.business_domain
(
    business_domain_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    domain_code        VARCHAR(100) NOT NULL UNIQUE,
    domain_name        VARCHAR(200) NOT NULL,
    description        TEXT,
    industry           VARCHAR(200),
    is_active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE ekr_business.business_domain IS
'Stores business domains used to associate enterprise assets, documents and knowledge with business context.';

COMMENT ON COLUMN ekr_business.business_domain.business_domain_id IS
'Primary key for the business domain.';
COMMENT ON COLUMN ekr_business.business_domain.domain_code IS
'Stable business domain code used by CLI, APIs and future UI, for example FINANCE or SALES.';
COMMENT ON COLUMN ekr_business.business_domain.domain_name IS
'Human-readable name of the business domain.';
COMMENT ON COLUMN ekr_business.business_domain.description IS
'Business description of the domain.';
COMMENT ON COLUMN ekr_business.business_domain.industry IS
'Optional industry classification when a domain is industry-specific.';
COMMENT ON COLUMN ekr_business.business_domain.is_active IS
'Indicates whether the business domain is active and available for assignment.';
COMMENT ON COLUMN ekr_business.business_domain.created_at IS
'Timestamp when the business domain record was created.';
COMMENT ON COLUMN ekr_business.business_domain.updated_at IS
'Timestamp when the business domain record was last updated.';

INSERT INTO ekr_business.business_domain
(domain_code, domain_name, description)
VALUES
('UNKNOWN', 'Unknown', 'Default domain when no business domain has been assigned.'),
('FINANCE', 'Finance', 'Financial management, accounting, reporting and treasury.'),
('SALES', 'Sales', 'Sales operations, revenue generation and customer acquisition.'),
('MARKETING', 'Marketing', 'Marketing campaigns, brand, demand generation and customer engagement.'),
('PROCUREMENT', 'Procurement', 'Supplier management, purchasing and sourcing.'),
('SUPPLY_CHAIN', 'Supply Chain', 'Planning, logistics, inventory and distribution.'),
('MANUFACTURING', 'Manufacturing', 'Production, operations and manufacturing processes.'),
('HUMAN_RESOURCES', 'Human Resources', 'People, recruitment, payroll and employee management.'),
('CUSTOMER_SERVICE', 'Customer Service', 'Customer support, service management and customer experience.'),
('LEGAL', 'Legal', 'Legal operations, contracts and compliance.'),
('RISK', 'Risk', 'Enterprise risk, controls and risk management.'),
('IT', 'Information Technology', 'Technology services, systems and infrastructure.'),
('EXECUTIVE', 'Executive', 'Executive reporting, strategy and corporate management.')
ON CONFLICT (domain_code) DO NOTHING;