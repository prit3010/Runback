"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-09 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "flow",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("repo_path", sa.String(), nullable=False),
        sa.Column("agent", sa.String(), nullable=False),
        sa.Column("active_version_id", sa.String(), nullable=False),
        sa.Column("schedule", sa.String(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "runner",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(), nullable=True),
        sa.Column("current_run_id", sa.String(), nullable=True),
        sa.Column("available_repos_json", sa.JSON(), nullable=True),
        sa.Column("claude_code_available", sa.Boolean(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "flowversion",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("flow_id", sa.String(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.String(), nullable=False),
        sa.Column("replay_mode", sa.String(), nullable=False),
        sa.Column("side_effect_policy", sa.String(), nullable=False),
        sa.Column("cache_policy_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["flow_id"], ["flow.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_flowversion_flow_id"), "flowversion", ["flow_id"], unique=False)
    op.create_table(
        "run",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("flow_id", sa.String(), nullable=True),
        sa.Column("flow_version_id", sa.String(), nullable=True),
        sa.Column("runner_id", sa.String(), nullable=True),
        sa.Column("run_kind", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("original_prompt", sa.String(), nullable=False),
        sa.Column("repo_path", sa.String(), nullable=False),
        sa.Column("workspace_path", sa.String(), nullable=True),
        sa.Column("root_branch_id", sa.String(), nullable=False),
        sa.Column("current_branch_id", sa.String(), nullable=False),
        sa.Column("failure_node_id", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["flow_id"], ["flow.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_run_flow_id"), "run", ["flow_id"], unique=False)
    op.create_table(
        "artifact",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("node_id", sa.String(), nullable=True),
        sa.Column("produced_by_node_id", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("content_preview", sa.String(), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("cache_policy_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_artifact_run_id"), "artifact", ["run_id"], unique=False)
    op.create_table(
        "checkpoint",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("branch_id", sa.String(), nullable=False),
        sa.Column("node_id", sa.String(), nullable=True),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("backend", sa.String(), nullable=False),
        sa.Column("git_ref", sa.String(), nullable=True),
        sa.Column("git_commit_hash", sa.String(), nullable=True),
        sa.Column("patch_path", sa.String(), nullable=True),
        sa.Column("workspace_path", sa.String(), nullable=False),
        sa.Column("diff_summary", sa.String(), nullable=True),
        sa.Column("file_hashes_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_checkpoint_branch_id"), "checkpoint", ["branch_id"], unique=False)
    op.create_index(op.f("ix_checkpoint_run_id"), "checkpoint", ["run_id"], unique=False)
    op.create_table(
        "replayattempt",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("source_node_id", sa.String(), nullable=False),
        sa.Column("source_checkpoint_id", sa.String(), nullable=False),
        sa.Column("parent_branch_id", sa.String(), nullable=False),
        sa.Column("new_branch_id", sa.String(), nullable=False),
        sa.Column("resume_prompt", sa.String(), nullable=False),
        sa.Column("user_context", sa.String(), nullable=True),
        sa.Column("generated_context", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("recommendation_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_replayattempt_new_branch_id"),
        "replayattempt",
        ["new_branch_id"],
        unique=False,
    )
    op.create_index(op.f("ix_replayattempt_run_id"), "replayattempt", ["run_id"], unique=False)
    op.create_table(
        "rungroup",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("parent_group_id", sa.String(), nullable=True),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["parent_group_id"], ["rungroup.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rungroup_run_id"), "rungroup", ["run_id"], unique=False)
    op.create_table(
        "sideeffectlog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("branch_id", sa.String(), nullable=False),
        sa.Column("node_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("external_ref", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("payload_preview", sa.String(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kind", "idempotency_key", name="uq_kind_key"),
    )
    op.create_index(
        op.f("ix_sideeffectlog_branch_id"),
        "sideeffectlog",
        ["branch_id"],
        unique=False,
    )
    op.create_index(op.f("ix_sideeffectlog_node_id"), "sideeffectlog", ["node_id"], unique=False)
    op.create_index(op.f("ix_sideeffectlog_run_id"), "sideeffectlog", ["run_id"], unique=False)
    op.create_table(
        "node",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("branch_id", sa.String(), nullable=False),
        sa.Column("group_id", sa.String(), nullable=True),
        sa.Column("claude_tool_use_id", sa.String(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=True),
        sa.Column("input_json", sa.JSON(), nullable=True),
        sa.Column("output_json", sa.JSON(), nullable=True),
        sa.Column("output_preview", sa.String(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("recovery_policy", sa.String(), nullable=False),
        sa.Column("classification_reason", sa.String(), nullable=True),
        sa.Column("classification_confidence", sa.Float(), nullable=True),
        sa.Column("checkpoint_before_id", sa.String(), nullable=True),
        sa.Column("checkpoint_after_id", sa.String(), nullable=True),
        sa.Column("cache_policy_json", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("raw_event_path", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["rungroup.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_node_branch_id"), "node", ["branch_id"], unique=False)
    op.create_index(
        op.f("ix_node_claude_tool_use_id"),
        "node",
        ["claude_tool_use_id"],
        unique=False,
    )
    op.create_index(op.f("ix_node_group_id"), "node", ["group_id"], unique=False)
    op.create_index(op.f("ix_node_run_id"), "node", ["run_id"], unique=False)
    op.create_table(
        "edge",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("branch_id", sa.String(), nullable=False),
        sa.Column("source_node_id", sa.String(), nullable=False),
        sa.Column("target_node_id", sa.String(), nullable=False),
        sa.Column("edge_type", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_edge_branch_id"), "edge", ["branch_id"], unique=False)
    op.create_index(op.f("ix_edge_run_id"), "edge", ["run_id"], unique=False)
    op.create_table(
        "nodeartifactedge",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("node_id", sa.String(), nullable=False),
        sa.Column("artifact_id", sa.String(), nullable=False),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifact.id"]),
        sa.ForeignKeyConstraint(["node_id"], ["node.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["run.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_nodeartifactedge_artifact_id"),
        "nodeartifactedge",
        ["artifact_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_nodeartifactedge_node_id"),
        "nodeartifactedge",
        ["node_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_nodeartifactedge_run_id"),
        "nodeartifactedge",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_nodeartifactedge_run_id"), table_name="nodeartifactedge")
    op.drop_index(op.f("ix_nodeartifactedge_node_id"), table_name="nodeartifactedge")
    op.drop_index(op.f("ix_nodeartifactedge_artifact_id"), table_name="nodeartifactedge")
    op.drop_table("nodeartifactedge")
    op.drop_index(op.f("ix_edge_run_id"), table_name="edge")
    op.drop_index(op.f("ix_edge_branch_id"), table_name="edge")
    op.drop_table("edge")
    op.drop_index(op.f("ix_node_run_id"), table_name="node")
    op.drop_index(op.f("ix_node_group_id"), table_name="node")
    op.drop_index(op.f("ix_node_claude_tool_use_id"), table_name="node")
    op.drop_index(op.f("ix_node_branch_id"), table_name="node")
    op.drop_table("node")
    op.drop_index(op.f("ix_sideeffectlog_run_id"), table_name="sideeffectlog")
    op.drop_index(op.f("ix_sideeffectlog_node_id"), table_name="sideeffectlog")
    op.drop_index(op.f("ix_sideeffectlog_branch_id"), table_name="sideeffectlog")
    op.drop_table("sideeffectlog")
    op.drop_index(op.f("ix_rungroup_run_id"), table_name="rungroup")
    op.drop_table("rungroup")
    op.drop_index(op.f("ix_replayattempt_run_id"), table_name="replayattempt")
    op.drop_index(op.f("ix_replayattempt_new_branch_id"), table_name="replayattempt")
    op.drop_table("replayattempt")
    op.drop_index(op.f("ix_checkpoint_run_id"), table_name="checkpoint")
    op.drop_index(op.f("ix_checkpoint_branch_id"), table_name="checkpoint")
    op.drop_table("checkpoint")
    op.drop_index(op.f("ix_artifact_run_id"), table_name="artifact")
    op.drop_table("artifact")
    op.drop_index(op.f("ix_run_flow_id"), table_name="run")
    op.drop_table("run")
    op.drop_index(op.f("ix_flowversion_flow_id"), table_name="flowversion")
    op.drop_table("flowversion")
    op.drop_table("runner")
    op.drop_table("flow")
