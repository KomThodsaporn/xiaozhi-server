FROM ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:server_latest
COPY ./models /opt/xiaozhi-esp32-server/models
COPY ./data /opt/xiaozhi-esp32-server/data
