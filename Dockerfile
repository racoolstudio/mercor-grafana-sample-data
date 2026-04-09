FROM grafana/grafana:latest

USER root

# Install SQLite plugin (baked in — no internet needed at runtime)
COPY frser-sqlite-datasource.zip /tmp/sqlite-plugin.zip
RUN mkdir -p /var/lib/grafana/plugins && \
    cd /var/lib/grafana/plugins && \
    unzip /tmp/sqlite-plugin.zip && \
    rm /tmp/sqlite-plugin.zip

# Bake in all provisioning (datasources + dashboards)
COPY grafana/provisioning /etc/grafana/provisioning

# Bake in the SQLite e-commerce database
COPY ecommerce.db /var/lib/grafana/ecommerce.db

# Fix permissions
RUN chown -R grafana:root /var/lib/grafana /etc/grafana/provisioning

USER grafana

ENV GF_SECURITY_ADMIN_USER=admin \
    GF_SECURITY_ADMIN_PASSWORD=admin123 \
    GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS=frser-sqlite-datasource
