FROM python:3.10-slim
ENV APP_HOME /app
ENV PORT 8084
WORKDIR $APP_HOME
COPY src/* ./
RUN pip install --no-cache-dir -r  requirements.txt
RUN apt-get update && apt-get install vim curl redis-tools -y
CMD python main.py