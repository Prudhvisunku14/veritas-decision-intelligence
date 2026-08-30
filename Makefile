.PHONY: bootstrap api ui test

bootstrap:
	python scripts/bootstrap.py

api:
	uvicorn backend.app.main:app --reload --port 8000

ui:
	streamlit run frontend/streamlit_app.py

test:
	pytest backend/tests -q
