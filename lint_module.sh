echo "Running ruff on project"
uv run ruff check
echo "Running ty on project"
uv run ty check . --config-file ./ty.toml
