FROM ubuntu:18.04
COPY . /app
RUN apt update && apt install -y firefox python3 python3-pip
COPY geckodriver /usr/bin
WORKDIR /app
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

CMD python3 /app/scrape_and_upload.py
