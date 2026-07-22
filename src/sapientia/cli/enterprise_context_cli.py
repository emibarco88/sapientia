import json
from dataclasses import asdict

from sapientia.services.enterprise_context_service import (
    EnterpriseContextService,
)


def run_enterprise_context(args):

    service = EnterpriseContextService()

    context = service.get_context(
        project_id=args.project_id,
        business_domain=args.business_domain,
    )

    print(
        json.dumps(
            asdict(context),
            indent=2,
            default=str,
        )
    )