from influxdb_client import InfluxDBClient, Point
from influxdb_client.domain.write_precision import WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import random
import time
from datetime import datetime, timedelta

INFLUX_URL   = "http://localhost:8086"
INFLUX_TOKEN = "myinfluxtoken123456"
INFLUX_ORG   = "myorg"
INFLUX_BUCKET = "iot"

SERVERS = ["web-01","web-02","api-01","api-02","db-primary","db-replica","cache-01","worker-01"]
SENSORS = {
    "sensor-A1": ("Warehouse A", "temperature", "humidity"),
    "sensor-A2": ("Warehouse A", "temperature", "humidity"),
    "sensor-B1": ("Warehouse B", "temperature", "humidity"),
    "sensor-C1": ("Office",      "temperature", "humidity"),
    "sensor-D1": ("Server Room", "temperature", "humidity"),
    "sensor-E1": ("Cold Storage","temperature", "humidity"),
}
SERVICES = ["api-gateway","auth-service","payment-service","notification-service",
            "search-service","recommendation-engine","analytics-service"]

def wait_for_influx(retries=20):
    import urllib.request, urllib.error
    for i in range(retries):
        try:
            urllib.request.urlopen(f"{INFLUX_URL}/health", timeout=3)
            return
        except Exception:
            print(f"  waiting for InfluxDB... ({i+1}/{retries})")
            time.sleep(3)
    raise RuntimeError("InfluxDB never became ready")

def build():
    wait_for_influx()
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    points = []
    now = datetime.utcnow()

    print("Generating server metrics (90 days)...")
    for server in SERVERS:
        base_cpu  = random.uniform(15, 60)
        base_mem  = random.uniform(30, 75)
        base_disk = random.uniform(20, 80)
        # hourly data points for 90 days
        for h in range(90 * 24):
            ts = now - timedelta(hours=h)
            hour = ts.hour
            # business hours spike
            load_mult = 1.0 + (0.5 if 8 <= hour <= 18 else 0.0) + random.uniform(-0.1, 0.2)
            cpu  = min(100, max(0, base_cpu  * load_mult + random.gauss(0, 5)))
            mem  = min(100, max(0, base_mem  * load_mult + random.gauss(0, 3)))
            disk = min(100, max(0, base_disk + h * 0.001 + random.gauss(0, 0.5)))  # disk grows slowly
            net_in  = max(0, random.lognormvariate(6, 1) * load_mult)
            net_out = max(0, net_in * random.uniform(0.3, 0.8))

            p = (Point("server_metrics")
                 .tag("host", server)
                 .field("cpu_usage",    float(round(cpu, 2)))
                 .field("memory_usage", float(round(mem, 2)))
                 .field("disk_usage",   float(round(disk, 2)))
                 .field("net_in_kbps",  float(round(net_in, 1)))
                 .field("net_out_kbps", float(round(net_out, 1)))
                 .time(ts, WritePrecision.S))
            points.append(p)

            if len(points) >= 3000:
                write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
                points = []

    print("Generating IoT sensor data (180 days)...")
    sensor_baselines = {
        "sensor-A1": (22, 55), "sensor-A2": (23, 52),
        "sensor-B1": (20, 60), "sensor-C1": (21, 45),
        "sensor-D1": (18, 40), "sensor-E1": (2, 80),
    }
    for sensor_id, (location, *_) in SENSORS.items():
        base_temp, base_hum = sensor_baselines[sensor_id]
        for h in range(180 * 24):
            ts = now - timedelta(hours=h)
            hour = ts.hour
            seasonal = 2 * (ts.timetuple().tm_yday / 365)
            daily    = 3 * abs(hour - 14) / 14
            temp = base_temp + seasonal - daily + random.gauss(0, 0.8)
            hum  = min(100, max(0, base_hum + random.gauss(0, 2)))
            pressure = 1013.25 + random.gauss(0, 5)
            co2 = max(400, 600 + (200 if 8 <= hour <= 18 else 0) + random.gauss(0, 30))

            p = (Point("iot_sensors")
                 .tag("sensor_id", sensor_id)
                 .tag("location", location)
                 .field("temperature",  float(round(temp, 2)))
                 .field("humidity",     float(round(hum, 2)))
                 .field("pressure_hpa", float(round(pressure, 2)))
                 .field("co2_ppm",      float(round(co2, 1)))
                 .time(ts, WritePrecision.S))
            points.append(p)

            if len(points) >= 3000:
                write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
                points = []

    print("Generating application metrics (30 days)...")
    for service in SERVICES:
        base_rps     = random.uniform(50, 500)
        base_latency = random.uniform(20, 200)
        for h in range(30 * 24):
            ts = now - timedelta(hours=h)
            hour = ts.hour
            traffic_mult = 1 + (0.8 if 9 <= hour <= 20 else -0.3) + random.uniform(-0.1, 0.1)
            rps      = max(0, base_rps * traffic_mult + random.gauss(0, 10))
            latency  = max(1, base_latency / traffic_mult + random.gauss(0, 15))
            err_rate = max(0, min(10, random.gauss(0.5, 0.3)))
            conns    = max(0, float(int(rps * random.uniform(0.5, 2.0))))

            p = (Point("app_metrics")
                 .tag("service", service)
                 .field("requests_per_sec",   float(round(rps, 2)))
                 .field("latency_ms",         float(round(latency, 2)))
                 .field("error_rate_pct",     float(round(err_rate, 3)))
                 .field("active_connections", float(conns))
                 .time(ts, WritePrecision.S))
            points.append(p)

            if len(points) >= 3000:
                write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
                points = []

    if points:
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)

    client.close()
    print("\nDone! IoT/Monitoring data ready in InfluxDB (bucket: iot)")

if __name__ == "__main__":
    build()
