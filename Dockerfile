FROM python:latest
WORKDIR /Priority3
COPY . /Priority3
RUN pip3 install -r requirements.txt
ENV FLASK_APP=main
ENV ACCESS_KEY=''
ENV SECRET_ACCESS_KEY=''
ENV AWS_REGION=''
ENV P3_QUEUE=''
ENV EMAIL=''
EXPOSE 8000
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8000"]