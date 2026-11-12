FROM python:3.10-slim
WORKDIR /app
RUN pip install --no-cache-dir pyzmq==25.1.1
COPY proxy.py .
CMD ["python", "proxy.py"]