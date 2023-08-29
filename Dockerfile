FROM python:3
RUN mkdir /app
WORKDIR /app

RUN apt-get update
RUN apt-get install -y locales locales-all
ENV LC_ALL ru_RU.UTF-8
ENV LANG ru_RU.UTF-8
ENV LANGUAGE ru_RU.UTF-8

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# https://github.com/fscdev/vkwave/issues/188
RUN pip install --no-cache-dir -U pydantic

COPY . .

CMD [ "python", "main.py"]