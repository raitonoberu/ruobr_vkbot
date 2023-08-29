FROM python:3-alpine
RUN mkdir /app
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# https://github.com/fscdev/vkwave/issues/188
RUN pip install --no-cache-dir -U pydantic

COPY . .
CMD [ "python", "main.py"]