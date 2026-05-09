from runback_server.ingest.ids import (
    artifact_id,
    branch_id,
    checkpoint_id,
    edge_id,
    group_id,
    label_with_short_id,
    new_id,
    node_id,
    run_id,
    sanitize_label,
)


def test_new_id_has_prefix_and_is_unique():
    first = new_id("foo")
    second = new_id("foo")
    assert first.startswith("foo_")
    assert first != second
    assert len(first) > 10


def test_typed_ids_have_expected_prefixes():
    assert run_id().startswith("run_")
    assert node_id().startswith("node_")
    assert group_id().startswith("grp_")
    assert edge_id().startswith("edge_")
    assert checkpoint_id().startswith("cp_")
    assert artifact_id().startswith("art_")
    assert branch_id().startswith("branch_")


def test_sanitize_label_replaces_unsafe_chars():
    assert sanitize_label("Read foo.py") == "Read_foo.py"
    assert sanitize_label("Bash: npm test") == "Bash__npm_test"
    assert sanitize_label("path/with/slashes") == "path_with_slashes"
    assert sanitize_label("  spaces  ") == "spaces"
    assert sanitize_label("") == "unlabeled"


def test_label_with_short_id_appends_suffix():
    out = label_with_short_id("Read foo.py", "node_01HXYZ123ABC")
    assert out.startswith("Read_foo.py_")
    assert len(out.split("_")[-1]) == 6
