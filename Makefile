.PHONY: install run dashboard test clean

install:
	pip install -e .[dev]

run:
	ouroboros run --entities 17 --mode terminal

dashboard:
	ouroboros dashboard

test:
	pytest eden_ecs/ ABRAXIS/tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist
