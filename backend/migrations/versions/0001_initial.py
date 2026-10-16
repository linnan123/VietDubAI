"""Phase 1 persistent production records."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None


def upgrade():
    op.create_table("projects", sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(200), nullable=False), sa.Column("description", sa.Text(), nullable=False))
    op.create_table("episodes", sa.Column("id", sa.String(36), primary_key=True), sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("source_path", sa.Text()), sa.Column("source_sha256", sa.String(64)), sa.Column("wav_path", sa.Text()), sa.Column("metadata_json", sa.Text()), sa.Column("approved", sa.Boolean(), nullable=False))
    op.create_index("ix_episodes_project_id", "episodes", ["project_id"])
    op.create_table("jobs", sa.Column("id", sa.String(36), primary_key=True), sa.Column("episode_id", sa.String(36), sa.ForeignKey("episodes.id"), nullable=False, unique=True), sa.Column("status", sa.String(20), nullable=False), sa.Column("attempts", sa.Integer(), nullable=False), sa.Column("error", sa.Text()), sa.Column("lease_until", sa.Integer(), nullable=False), sa.Column("created_at", sa.Text(), nullable=False))
    op.create_index("ix_jobs_status", "jobs", ["status"])


def downgrade():
    op.drop_table("jobs")
    op.drop_table("episodes")
    op.drop_table("projects")
