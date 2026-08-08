from __future__ import annotations

from pathlib import Path

import pytest

from nocturnix.assistant.reference_analysis import (
    MAX_EXCERPT_LENGTH,
    _annotation_matches,
    _expr_name,
    _normalize_extensions,
    _source_line,
    analyze_repository_references,
)


def test_analyze_repository_references_returns_empty_for_blank_symbol(
    tmp_path: Path,
) -> None:
    assert (
        analyze_repository_references(
            tmp_path,
            "   ",
        )
        == []
    )


def test_analyze_repository_references_rejects_missing_root(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing"

    with pytest.raises(
        ValueError,
        match="does not exist or is not a directory",
    ):
        analyze_repository_references(
            missing,
            "Target",
        )


def test_normalize_extensions_defaults_and_formats_values() -> None:
    assert _normalize_extensions(None) == [".py"]

    assert _normalize_extensions(
        [
            "py",
            ".MD",
            "  txt  ",
            "",
            "   ",
        ]
    ) == [
        ".py",
        ".md",
        ".txt",
    ]

    assert _normalize_extensions(["", "   "]) == [".py"]


def test_reference_analysis_finds_python_reference_types(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()

    source = repository_root / "references.py"

    source.write_text(
        "\n".join(
            [
                "import Target",
                "from package import Target",
                "",
                "@Target",
                "class Child(Target):",
                "    value: Target",
                "",
                "    @Target",
                "    def method(",
                "        self,",
                "        arg: Target,",
                "        *args: Target,",
                "        flag: Target,",
                "        **kwargs: Target,",
                "    ) -> Target:",
                "        Target()",
                "        instance.Target",
                "        return Target",
                "",
            ]
        ),
        encoding="utf-8",
    )

    results = analyze_repository_references(
        repository_root,
        "Target",
    )

    reference_types = {item.reference_type for item in results}

    assert "import" in reference_types
    assert "from-import" in reference_types
    assert "inheritance" in reference_types
    assert "decorator" in reference_types
    assert "annotation" in reference_types
    assert "call" in reference_types
    assert "attribute" in reference_types
    assert "name" in reference_types

    assert all(item.path == "references.py" for item in results)


def test_reference_analysis_supports_import_aliases(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()

    source = repository_root / "aliases.py"

    source.write_text(
        "\n".join(
            [
                "import package as Target",
                "from package import value as Target",
                "",
            ]
        ),
        encoding="utf-8",
    )

    results = analyze_repository_references(
        repository_root,
        "Target",
    )

    assert {item.reference_type for item in results} == {
        "import",
        "from-import",
    }


def test_reference_analysis_matches_import_module_root(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()

    source = repository_root / "imports.py"

    source.write_text(
        "\n".join(
            [
                "import Target.submodule",
                "from Target.module import something",
                "",
            ]
        ),
        encoding="utf-8",
    )

    results = analyze_repository_references(
        repository_root,
        "Target",
    )

    assert len(results) == 2
    assert results[0].reference_type == "import"
    assert results[1].reference_type == "from-import"


def test_reference_analysis_falls_back_for_invalid_python(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()

    source = repository_root / "broken.py"

    source.write_text(
        ("def broken(:\n    Target = 1\n    print(Target)\n"),
        encoding="utf-8",
    )

    results = analyze_repository_references(
        repository_root,
        "Target",
    )

    assert len(results) == 2

    assert all(item.reference_type == "text match" for item in results)


def test_reference_analysis_supports_non_python_extensions(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()

    text_file = repository_root / "notes.txt"

    text_file.write_text(
        ("No match here\nTarget appears here\nTarget appears again\n"),
        encoding="utf-8",
    )

    results = analyze_repository_references(
        repository_root,
        "Target",
        extensions=["txt"],
    )

    assert len(results) == 2
    assert all(item.reference_type == "text match" for item in results)


def test_reference_analysis_ignores_hidden_and_ignored_directories(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()

    visible = repository_root / "visible.py"
    visible.write_text(
        "Target()\n",
        encoding="utf-8",
    )

    hidden_dir = repository_root / ".hidden"
    hidden_dir.mkdir()
    (hidden_dir / "hidden.py").write_text(
        "Target()\n",
        encoding="utf-8",
    )

    git_dir = repository_root / ".git"
    git_dir.mkdir()
    (git_dir / "config.py").write_text(
        "Target()\n",
        encoding="utf-8",
    )

    cache_dir = repository_root / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "cached.py").write_text(
        "Target()\n",
        encoding="utf-8",
    )

    results = analyze_repository_references(
        repository_root,
        "Target",
    )

    assert results
    assert {item.path for item in results} == {
        "visible.py",
    }


def test_reference_analysis_respects_limit(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()

    for index in range(5):
        source = repository_root / f"{index}.py"

        source.write_text(
            "Target()\nTarget()\n",
            encoding="utf-8",
        )

    results = analyze_repository_references(
        repository_root,
        "Target",
        limit=3,
    )

    assert len(results) == 3


def test_reference_analysis_results_are_sorted(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()

    second = repository_root / "b.py"
    second.write_text(
        "Target()\n",
        encoding="utf-8",
    )

    first = repository_root / "a.py"
    first.write_text(
        "Target()\n",
        encoding="utf-8",
    )

    results = analyze_repository_references(
        repository_root,
        "Target",
    )

    paths = [item.path for item in results]

    assert paths == sorted(paths)


def test_long_excerpt_is_truncated(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()

    source = repository_root / "long.txt"

    source.write_text(
        "Target " + ("x" * 500),
        encoding="utf-8",
    )

    results = analyze_repository_references(
        repository_root,
        "Target",
        extensions=[".txt"],
    )

    assert len(results) == 1

    assert len(results[0].excerpt) <= MAX_EXCERPT_LENGTH + 1


def test_source_line_handles_valid_and_invalid_indexes() -> None:
    lines = [
        "first",
        "second",
    ]

    assert (
        _source_line(
            lines,
            1,
        )
        == "first"
    )

    assert (
        _source_line(
            lines,
            2,
        )
        == "second"
    )

    assert (
        _source_line(
            lines,
            0,
        )
        == ""
    )

    assert (
        _source_line(
            lines,
            3,
        )
        == ""
    )


def test_expr_name_handles_names_and_attributes() -> None:
    import ast

    name = ast.parse(
        "Target",
        mode="eval",
    ).body

    attribute = ast.parse(
        "package.Target",
        mode="eval",
    ).body

    nested = ast.parse(
        "package.module.Target",
        mode="eval",
    ).body

    call = ast.parse(
        "Target()",
        mode="eval",
    ).body

    assert _expr_name(name) == "Target"
    assert _expr_name(attribute) == "package.Target"
    assert _expr_name(nested) == ("package.module.Target")
    assert _expr_name(call) is None


def test_annotation_matching_supports_nested_annotation_forms() -> None:
    import ast

    annotations = [
        "Target",
        "package.Target",
        "list[Target]",
        "tuple[Target, str]",
        "list[tuple[Target, str]]",
        "Annotated(Target)",
    ]

    for source in annotations:
        node = ast.parse(
            source,
            mode="eval",
        ).body

        assert _annotation_matches(
            "Target",
            node,
        )

    unrelated = ast.parse(
        "list[str]",
        mode="eval",
    ).body

    assert not _annotation_matches(
        "Target",
        unrelated,
    )
