FROM python:3.9

WORKDIR /app

COPY . /app

RUN chmod +x /app/init.sh

RUN pip install --no-cache-dir -r requirements.txt

CMD ["/app/init.sh"]
