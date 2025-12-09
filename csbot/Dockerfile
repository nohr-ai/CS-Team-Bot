FROM python:3.10.14-alpine3.19

WORKDIR /usr/src/csbot
COPY . .

RUN python3 -m pip install --no-cache-dir -r requirements.txt
CMD ["python", "bot.py"]