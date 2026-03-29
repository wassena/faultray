.PHONY: test lint typecheck mutate quality

test:
	python3 -m pytest tests/ -q --tb=short

test-fast:
	python3 -m pytest tests/ -x -q --tb=short

lint:
	ruff check src/ tests/

typecheck:
	python3 -m mypy src/faultray/model/ --ignore-missing-imports

mutate:
	python3 -m mutmut run

mutate-results:
	python3 -m mutmut results

quality: lint typecheck test
	@echo "All quality checks passed"
