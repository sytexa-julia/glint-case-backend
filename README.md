# Glint Case Study: Backend

## Getting started
1. Create and activate venv
2. `pip install -r requirements.txt`
3. `uvicorn main:app`

## Configuration
You can use environment variable `CORS_ORIGINS` to specify a space-separated list of front-end base URLs to allow.

## Notes
This is a simple FastAPI project with one unprotected GET endpoint at `/waves/max_height`.

**For a real application, I would usually implement:**
- Authentication + Authorization
- Logging
- Unit + Integration Tests
