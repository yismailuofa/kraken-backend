#### For the frontend repo see: [kraken-frontend](https://github.com/yismailuofa/kraken-frontend)

## Running the App locally

1. Start mongoDB (depends on your OS)
2. Navigate to the root directory
3. Start the api server with `uvicorn api.main:app --host 0.0.0.0 --port 80 --log-level debug --reload`
4. Go to http://localhost/docs

## Running the App on Docker

1. Navigate to the root directory
2. Run `docker compose -f docker-compose.dev.yml -d --build up`
3. Go to http://localhost/docs

## Running Tests

1. Navigate to the root directory
2. Run `python3 -m unittest`
3. To run a specific file run you can specify it like so `python3 -m unittest api/tests/test_projects.py`

## Generating Coverage

1. Run `coverage run --source=api -m unittest`
2. Run `coverage report > coverage.txt` to save the coverage report to a file.
3. Run `coverage html` to generate a html report.
