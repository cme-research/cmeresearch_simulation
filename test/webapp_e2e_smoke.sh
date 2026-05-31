#!/bin/bash
# End-to-end webapp smoke test.
#
# Verifies the ROS↔MQTT chain wired by the `webapp` docker-compose profile:
#   webots_sim (mecanum controller publishes /base_mecanum_controller/odometry)
#     → nav_stack (mqtt_bridge_node, RosToMqttBridge: ~/base/odometry)
#     → mosquitto broker
#     → MQTT subscriber here
#
# Run AFTER `docker compose --profile webapp up -d`. Waits for the broker
# to accept connections, then listens for an Odometry message on the
# expected MQTT topic. Exit 0 = pass, 1 = fail.
set -euo pipefail

TOPIC="cmeresearch/cmexaiii-001/base/odometry"
BROKER_HOST="${MQTT_HOST:-localhost}"
BROKER_PORT="${MQTT_PORT:-1883}"
BROKER_TIMEOUT_S="${BROKER_TIMEOUT_S:-30}"
MSG_TIMEOUT_S="${MSG_TIMEOUT_S:-180}"

echo "==> waiting up to ${BROKER_TIMEOUT_S}s for broker at ${BROKER_HOST}:${BROKER_PORT}"
deadline=$(( $(date +%s) + BROKER_TIMEOUT_S ))
until mosquitto_sub -h "${BROKER_HOST}" -p "${BROKER_PORT}" \
        -t '$SYS/broker/uptime' -C 1 -W 3 -i e2e_smoke_probe >/dev/null 2>&1; do
  if (( $(date +%s) > deadline )); then
    echo "::error::broker never came up at ${BROKER_HOST}:${BROKER_PORT}"
    exit 1
  fi
  sleep 1
done
echo "==> broker reachable"

echo "==> waiting up to ${MSG_TIMEOUT_S}s for first message on ${TOPIC}"
if msg=$(timeout "${MSG_TIMEOUT_S}" mosquitto_sub \
      -h "${BROKER_HOST}" -p "${BROKER_PORT}" \
      -t "${TOPIC}" -C 1 -i e2e_smoke_consumer 2>&1); then
  echo "==> PASS — received message on ${TOPIC}:"
  echo "${msg}" | head -c 500
  echo
  exit 0
fi

echo "::error::no message on ${TOPIC} within ${MSG_TIMEOUT_S}s"
echo "::group::diagnostics"
echo "--- mosquitto_sub on \$SYS/broker/clients/connected ---"
mosquitto_sub -h "${BROKER_HOST}" -p "${BROKER_PORT}" \
  -t '$SYS/broker/clients/connected' -C 1 -W 3 -i e2e_smoke_diag || true
echo "--- topics currently published ---"
timeout 5 mosquitto_sub -h "${BROKER_HOST}" -p "${BROKER_PORT}" \
  -t '#' -v -i e2e_smoke_diag_all 2>/dev/null | head -50 || true
echo "::endgroup::"
exit 1
