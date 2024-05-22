FROM python:3.9.15

# RUN apt-get update \
#     && apt-get install -y \
#     libpq-dev \
#     gcc \
#     libgl1 \
#     python3-opencv \
#     && apt-get autoremove -y \
#     && apt-get autoclean -y \
#     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./automation/api /app

RUN python3 -m pip install -r requirements.txt

CMD ["bash", "start.sh"]
