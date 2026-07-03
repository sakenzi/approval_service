from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=100), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reviewer_user_ids", sa.String(length=1000), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=100), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_approval_requests_request_hash"), "approval_requests", ["request_hash"], unique=True)
    op.create_index(op.f("ix_approval_requests_workspace_id"), "approval_requests", ["workspace_id"], unique=False)

    op.create_table(
        "approval_decisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("approval_request_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=100), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("actor_user_id", sa.String(length=100), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("approval_decisions")
    op.drop_index(op.f("ix_approval_requests_request_hash"), table_name="approval_requests")
    op.drop_index(op.f("ix_approval_requests_workspace_id"), table_name="approval_requests")
    op.drop_table("approval_requests")
