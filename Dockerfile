FROM python:3-alpine

ADD requirements.txt /requirements.txt
ADD validator.py /validator.py

RUN pip install -r /requirements.txt && \
    rm -rf ~/.cache/pip

ENTRYPOINT ["python", "/validator.py"]
