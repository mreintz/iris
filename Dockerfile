FROM alpine:3.7
RUN apk add --update \
        python \
        py-pip \
        && rm -rf /var/cache/apk/*

EXPOSE 8099/tcp

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY iris.py iris.xml iris_download.xml /
COPY static/kalenderstil.css static/trash.ico /static/

CMD ["/usr/bin/python", "/iris.py"]