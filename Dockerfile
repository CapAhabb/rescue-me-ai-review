FROM python:3.13-slim

WORKDIR /app
COPY backend ./backend
ENV PYTHONPATH=/app/backend

EXPOSE 8088
CMD ["python", "-c", "from rescue_me.api import run; run(host='0.0.0.0')"]
