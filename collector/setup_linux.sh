#!/bin/bash
# setup_linux.sh
# chmod 755 setup_linux.sh

echo "========================================================"
echo "rsyslog set up"
echo "========================================================"

sudo apt update
sudo apt install -y rsyslog systemd curl

cat << EOF | sudo tee /etc/rsyslog.d/01-json-parser.conf
template(name="json-template"
  type="list") {
    constant(value="{")
      constant(value="\"@timestamp\":\"")     property(name="timereported" dateFormat="rfc3339")
      constant(value="\",\"@version\":\"1")
      constant(value="\",\"message\":\"")     property(name="msg" format="json")
      constant(value="\",\"sysloghost\":\"")  property(name="hostname")
      constant(value="\",\"formhost-ip\":\"")  property(name="fromhost-ip")
      constant(value="\",\"severity\":\"")    property(name="syslogseverity-text")
      constant(value="\",\"facility\":\"")    property(name="syslogfacility-text")
      constant(value="\",\"programname\":\"") property(name="programname")
      constant(value="\",\"procid\":\"")      property(name="procid")
      constant(value="\",\"structured-data\":\"") property(name="structured-data")
      constant(value="\",\"protocol-version\":\"") property(name="protocol-version")
      constant(value="\",\"app-name\":\"")   property(name="app-name")
      constant(value="\",\"timegenerated\":\"")     property(name="timegenerated")
    constant(value="\"}\n")
}
EOF

cat << EOF | sudo tee /etc/rsyslog.d/60-fluentd.conf
*.*    @@localhost:5140;json-template
EOF

sudo systemctl restart rsyslog

# 기존의 Fluentd 설치 및 설정 부분은 Dockerfile로 이동했으므로 삭제
# echo "========================================================"
# echo "Starting install Fluentd"
# echo "========================================================"

# curl -fsSL https://toolbelt.treasuredata.com/sh/install-ubuntu-jammy-fluent-package5.sh | sh
# sudo systemctl start fluentd

# echo "========================================================"
# echo "setup Fluentd"
# echo "========================================================"

# sudo cp /etc/fluent/fluentd.conf /etc/fluent/fluentd.conf.bak

# cat << EOF | sudo tee /etc/fluent/fluentd.conf
# <source>
#   @type tcp
#   port 5140
#   bind 0.0.0.0
#   tag teiren.linux
#   <parse>
#     @type json
#   </parse>
# </source>

# <match teiren.linux>
#   @type http
#   endpoint http://127.0.0.1:8088/linux_log
#   json_array true
#   <format>
#     @type json
#   </format>
#   <buffer>
#     flush_interval 10s
#   </buffer>
# </match>

# EOF

# sudo systemctl restart fluentd
