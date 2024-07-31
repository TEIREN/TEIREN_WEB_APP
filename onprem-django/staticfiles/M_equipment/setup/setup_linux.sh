#!/bin/bash
# setup_linux.sh
# chmod 755 setup_linux.sh

echo "========================================================"
echo "rsysloh set up"
echo "========================================================"

sudo apt update
sudo apt install -y rsyslog
sudo apt install systemd
sudo apt install curl

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
*.*	@@localhost:{agent_port};json-template
EOF

sudo systemctl restart rsyslog

echo "========================================================"
echo "Starting install Fluentd"
echo "========================================================"

curl -fsSL https://toolbelt.treasuredata.com/sh/install-ubuntu-jammy-fluent-package5.sh | sh
sudo systemctl start fluentd

echo "========================================================"
echo "setup Fluentd"
echo "========================================================"

sudo cp /etc/fluent/fluentd.conf /etc/fluent/fluentd.conf.bak

cat << EOF | sudo tee /etc/fluent/fluentd.conf
<source>
  @type tcp
  port {agent_port}
  bind 127.0.0.1
  tag {tag_name}
  <parse>
    @type json
  </parse>
</source>

<match {tag_name}>
	@type http
	endpoint http://{teiren_server_ip}:8088/collect_log/linux/{tag_name}
	json_array true
	<format>
	  @type json
	</format>
	<buffer>
	  flush_interval 10s
	</buffer>
</match>

EOF

sudo systemctl restart fluentd