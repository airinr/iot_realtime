import streamlit as st
import pandas as pd
import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime

# -------------------------------------------------------------
# MANUAL MQTT SETTINGS (Laptop)
# -------------------------------------------------------------
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
TOPIC_SENSOR = "iot/class/session5/sensor"
TOPIC_OUTPUT = "iot/class/session5/output"


# -------------------------------------------------------------
# SESSION STATE INIT (WAJIB — AGAR TIDAK ERROR)
# -------------------------------------------------------------
if "connected" not in st.session_state:
    st.session_state.connected = False

if "logs" not in st.session_state:
    st.session_state.logs = []

if "last_data" not in st.session_state:
    st.session_state.last_data = None

if "mqtt" not in st.session_state:
    st.session_state.mqtt = None


# -------------------------------------------------------------
# MQTT CALLBACKS
# -------------------------------------------------------------
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        st.session_state.connected = True
        client.subscribe(TOPIC_SENSOR)
        print("Connected to MQTT broker")
    else:
        st.session_state.connected = False
        print("MQTT connection failed")


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        ts = datetime.now().strftime("%H:%M:%S")

        row = {"ts": ts, "temp": data.get("temp"), "hum": data.get("hum")}

        # UPDATE SESSION STATE AMAN (karena ini POLLING, bukan THREAD)
        st.session_state.last_data = row
        st.session_state.logs.append(row)

    except Exception as e:
        print("Parse error:", e)


# -------------------------------------------------------------
# START MQTT CLIENT — TANPA THREAD (NO ERROR)
# -------------------------------------------------------------
if st.session_state.mqtt is None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    st.session_state.mqtt = client


# -------------------------------------------------------------
# STREAMLIT UI
# -------------------------------------------------------------
st.title("🔥 IoT Realtime MQTT Dashboard — Stable Version")

left, right = st.columns([1, 2])

# ===================== LEFT PANEL ============================
with left:
    st.subheader("Connection Status")
    st.metric("MQTT Connected", "Yes" if st.session_state.connected else "No")
    st.metric("Broker", MQTT_BROKER)

    st.subheader("Last Sensor Reading")
    if st.session_state.last_data:
        st.write(st.session_state.last_data)
    else:
        st.info("Waiting for data...")

    st.subheader("Manual Command")
    if st.button("Send ALERT_ON"):
        st.session_state.mqtt.publish(TOPIC_OUTPUT, "ALERT_ON")
        st.success("Sent ALERT_ON")

    if st.button("Send ALERT_OFF"):
        st.session_state.mqtt.publish(TOPIC_OUTPUT, "ALERT_OFF")
        st.success("Sent ALERT_OFF")

    st.subheader("Download Logs")
    df = pd.DataFrame(st.session_state.logs)
    st.download_button("Download CSV", df.to_csv().encode("utf-8"), "log.csv")


# ===================== RIGHT PANEL ===========================
with right:
    st.subheader("Realtime Chart (Temp & Humidity)")

    df = pd.DataFrame(st.session_state.logs)

    if len(df) >= 2:
        st.line_chart(df.set_index("ts")[["temp", "hum"]])
    else:
        st.info("No data yet. Waiting for ESP32...")


# -------------------------------------------------------------
# MQTT LOOP POLLING (AMAN)
# -------------------------------------------------------------
st.session_state.mqtt.loop(timeout=0.1)

# auto refresh
time.sleep(1)
st.rerun()
