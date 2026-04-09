FROM grafana/grafana:latest

USER root
COPY frser-sqlite-datasource.zip /tmp/sqlite-plugin.zip
RUN mkdir -p /var/lib/grafana/plugins && \
    cd /var/lib/grafana/plugins && \
    unzip /tmp/sqlite-plugin.zip && \
    rm /tmp/sqlite-plugin.zip

USER grafana
