#### For the frontend repo see: [kraken-frontend](https://github.com/yismailuofa/kraken-frontend)

## Running the app locally

1. Start mongoDB (depends on your OS)
2. Start the api server with `uvicorn api.main:app --host 0.0.0.0 --port 80 --log-level debug --reload`

## Running the app on Docker

1. `docker-compose up -d`
