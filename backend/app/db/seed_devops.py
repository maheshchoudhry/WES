"""Seed environment profiles and deployment targets (Sprint 15).

The four standard environments (development → testing → staging → production) with
production Founder-gated, plus one deployment target per environment. Idempotent.
"""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.devops_enums import DeployStrategy
from app.models.devops import DeploymentTarget, EnvironmentProfile

# name, display_name, requires_approval, strategy
ENVIRONMENTS = [
    ("development", "Development", False, DeployStrategy.STANDARD),
    ("testing", "Testing", False, DeployStrategy.STANDARD),
    ("staging", "Staging", False, DeployStrategy.BLUE_GREEN),
    ("production", "Production", True, DeployStrategy.ROLLING),
]


def seed_devops(db: Session) -> bool:
    """Seed environments + targets. Idempotent."""
    if db.scalar(select(EnvironmentProfile).where(EnvironmentProfile.name == "production")):
        return False
    for i, (name, display, approval, strategy) in enumerate(ENVIRONMENTS):
        db.add(
            EnvironmentProfile(
                name=name,
                display_name=display,
                requires_approval=approval,
                strategy=strategy,
                variables=json.dumps({"WES_ENV": name}),
                position=i,
            )
        )
        db.add(
            DeploymentTarget(
                environment=name,
                name=f"{display} target",
                url=f"https://{name}.wes.local",
                strategy=strategy,
                requires_approval=approval,
            )
        )
    db.flush()
    return True
