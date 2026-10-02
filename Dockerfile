FROM python:3.11-slim
WORKDIR /app
COPY . .
ENV PORT=8000
EXPOSE 8000
CMD ["python3", "src/server.py"]
