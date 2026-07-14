"""enable row-level security on all public tables

Supabase auto-exposes a PostgREST REST API over the ``public`` schema, reachable
by anyone holding the project's anon key. With RLS disabled, the ``anon`` /
``authenticated`` roles behind that key can read, edit, and delete every row —
which is what Supabase's security advisor flags as ``rls_disabled_in_public``.

This app never uses that PostgREST surface: the frontend ships as fully static
baked JSON (Cloudflare Pages, no runtime DB), and all ingest/serving happens over
the direct ``DATABASE_URL`` connection as the ``postgres`` role, which has
``BYPASSRLS``. So enabling RLS with **no policies** closes the anon API completely
(deny-all) while leaving the ETL and in-process bake untouched.

We use plain ``ENABLE`` (not ``FORCE``) so the table owner and BYPASSRLS roles
still get through; only the anon/authenticated PostgREST roles are locked out.
PostGIS's ``spatial_ref_sys`` is intentionally excluded — it is an
extension-managed system table (see ``_POSTGIS_TABLES`` in ``alembic/env.py``).

Revision ID: e7b3a91c4d20
Revises: 0b06d8e2345c
Create Date: 2026-07-14 18:45:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e7b3a91c4d20'
down_revision: Union[str, Sequence[str], None] = '0b06d8e2345c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Every application table in the public schema. spatial_ref_sys is deliberately
# omitted (PostGIS-managed; not ours to secure).
_TABLES: tuple[str, ...] = (
    "data_source",
    "taxon",
    "tree",
    "climate_profile",
    "conservation_assessment",
    "genetic_resource",
    "name_alias",
    "occurrence",
    "photo",
    "phylogeny_node",
    "range_region",
    "trait",
    "use",
)


def upgrade() -> None:
    """Enable RLS on every public table (no policies == deny-all for anon)."""
    for table in _TABLES:
        op.execute(f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY;')


def downgrade() -> None:
    """Disable RLS, reopening the tables to the anon PostgREST API."""
    for table in _TABLES:
        op.execute(f'ALTER TABLE public."{table}" DISABLE ROW LEVEL SECURITY;')
