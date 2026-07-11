# Incident Triage

Search and AI assistant for incident triage (FastAPI + SQLite FTS + OpenAI).

## Data generation

Synthetic incident data lives at `data/incidents.json` (300 records). The file is pre-generated and committed to the repo.

If the file is missing, generate it once before ingesting:

```bash
python3 generate_data.py
```

If `data/incidents.json` already exists, the script prints a skip message and exits without overwriting.
