# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Chris <goabonga@pm.me>

"""Unit tests for Jinja2 email template renderer."""

from pathlib import Path
from textwrap import dedent

from shomer.email.renderer import create_env, render_template


class TestCreateEnv:
    """Tests for create_env()."""

    def test_returns_environment(self, tmp_path: Path) -> None:
        env = create_env(tmp_path)
        assert env is not None

    def test_autoescape_enabled(self, tmp_path: Path) -> None:
        env = create_env(tmp_path)
        assert callable(env.autoescape) or env.autoescape is True


class TestRenderTemplate:
    """Tests for render_template()."""

    def test_renders_simple_template(self, tmp_path: Path) -> None:
        (tmp_path / "hello.html").write_text("Hello {{ name }}!")
        result = render_template("hello.html", {"name": "World"}, template_dir=tmp_path)
        assert result == "Hello World!"

    def test_autoescapes_html(self, tmp_path: Path) -> None:
        (tmp_path / "escape.html").write_text("{{ value }}")
        result = render_template(
            "escape.html", {"value": "<script>alert(1)</script>"}, template_dir=tmp_path
        )
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_renders_with_block_inheritance(self, tmp_path: Path) -> None:
        (tmp_path / "base.html").write_text(
            dedent("""\
            <html>{% block content %}{% endblock %}</html>""")
        )
        (tmp_path / "child.html").write_text(
            dedent("""\
            {% extends "base.html" %}
            {% block content %}Hi {{ name }}{% endblock %}""")
        )
        result = render_template("child.html", {"name": "Alice"}, template_dir=tmp_path)
        assert "<html>Hi Alice</html>" == result

    def test_empty_context(self, tmp_path: Path) -> None:
        (tmp_path / "static.html").write_text("No variables here.")
        result = render_template("static.html", {}, template_dir=tmp_path)
        assert result == "No variables here."
