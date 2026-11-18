.PHONY: api web test lint eval clean

api:
	uvicorn meridian.api.server:app --reload --host 0.0.0.0 --port 8000

web:
	cd web && npm run dev

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/
	mypy src/

eval:
	python -m meridian.evals.runner

clean:
	rm -rf dist/ build/ web/dist/
