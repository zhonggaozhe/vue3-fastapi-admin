from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

jsonb = JSONB().with_variant(JSON(), "sqlite")

