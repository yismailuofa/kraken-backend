# 
FROM python:3.9

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./api /code/api

# 
CMD ["uvicorn", "api.main:app", \
    "--host", "0.0.0.0", \ 
    "--port","443", \
    "--ssl-keyfile", "/etc/letsencrypt/live/33db9.yeg.rac.sh/privkey.pem", \
    "--ssl-certfile", "/etc/letsencrypt/live/33db9.yeg.rac.sh/fullchain.pem"]