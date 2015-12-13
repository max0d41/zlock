FROM alpine:3.2
COPY setup.py /zlock/
RUN apk add --update python libstdc++ python-dev py-setuptools ca-certificates build-base && \
    mkdir /zlock/zlock && touch /zlock/zlock/__init__.py && \
    python /zlock/setup.py develop && rm -rf /zlock && \
    apk del --purge python-dev py-setuptools ca-certificates build-base && rm -rf /var/cache/apk/*
COPY zlock/__main__.py zlock/__init__.py /zlock/
CMD python -m zlock
