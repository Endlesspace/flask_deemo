FROM sqw_venv:latest
MAINTAINER SQW
WORKDIR /home/sqw
COPY . .
EXPOSE 5000
#CMD ["python", "./socketio_deemo.py"]
ENTRYPOINT ["./boot.sh"]
