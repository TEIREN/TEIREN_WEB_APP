import subprocess
import logging
from fastapi import HTTPException
# /home/ubuntu/TEIREN_WEB_APP/collector/fluentd_deployment.py:80: SyntaxWarning: invalid escape sequence '\d' 이런 경고가 뜨긴 함

class FluentdDeployment:
    def __init__(self, conf_file_path='/etc/fluent/fluentd.conf'):
        try:
            self.conf_file_path = conf_file_path
        except Exception as e:
            logging.error(f"Error initializing FluentdDeployment: {str(e)}")
            raise

    async def configure_fluentd(self, config, system, TAG_NAME):
        try:
            if config['new_log_tag'] != TAG_NAME:
                raise HTTPException(status_code=400, detail="TAG_NAME과 new_log_tag 값이 동일하여야 합니다.")
            if system == 'genian':
                new_conf_text = self._genian_conf(config)
            elif system == 'fortigate':
                new_conf_text = self._fortigate_conf(config)
            else:
                new_conf_text = self._default_conf(config)

            try:
                with open(self.conf_file_path, 'a') as file:
                    file.write(new_conf_text)
            except Exception as e:
                logging.error(f"Failed to write to the configuration file: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to write to the configuration file: {e}")

            try:
                subprocess.run(['sudo', '/bin/systemctl', 'restart', 'fluentd'], check=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to restart Fluentd service: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to restart Fluentd service: {e}")

            return {"status": "success", "message": "Fluentd service restarted and configuration updated successfully"}
        except Exception as e:
            logging.error(f"Error configuring Fluentd: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error configuring Fluentd: {str(e)}")

    def _genian_conf(self, config):
        try:
            new_endpoint = f"http://localhost:8088/collect_log/genian/{config['new_log_tag']}"
            return f"""
<source>
  @type udp
  port {config['new_dst_port']}
  bind {config['new_source_ip']}
  format /<(\d+)>(?<timestamp>[^ ]+ [^ ]+) (?<loglevel>[^ ]+) (?<logid>[^ ]+) (?<ip>[^ ]+) (?<mac>[^ ]+) (?<fullmsg>[^ ]+)(?<message>.+)/
  time_format %Y-%m-%d %H:%M:%S
  tag {config['new_log_tag']}
</source>

<filter {config['new_log_tag']}>
  @type record_transformer
  enable_ruby true
  <record>
    log_id ${{record["logid"]}}
    timestamp ${{record["timestamp"]}}
    log_level ${{record["loglevel"]}}
    ip ${{record["ip"]}}
    mac ${{record["mac"]}}
    fullmsg ${{record["fullmsg"]}}
    message ${{record["message"]}}
  </record>
</filter>

<match {config['new_log_tag']}>
  @type http
  endpoint {new_endpoint}
  json_array true
  <format>
    @type json
  </format>
  <buffer>
    flush_interval 10s
  </buffer>
</match>
"""
        except Exception as e:
            logging.error(f"Error generating genian configuration: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating genian configuration: {str(e)}")

    def _fortigate_conf(self, config):
        try:
            new_endpoint = f"http://localhost:8088/collect_log/fortigate/{config['new_log_tag']}"
            return f"""
<source>
  @type udp
  port {config['new_dst_port']}
  bind {config['new_source_ip']}
  <parse>
    @type none
  </parse>
  tag {config['new_log_tag']}
</source>

<match {config['new_log_tag']}>
  @type http
  endpoint {new_endpoint}
  json_array true
  <format>
    @type json
  </format>
  <buffer>
    flush_interval 10s
  </buffer>
</match>
"""
        except Exception as e:
            logging.error(f"Error generating fortigate configuration: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating fortigate configuration: {str(e)}")

    def _default_conf(self, config):
        try:
            new_endpoint = f"http://localhost:8088/collect_log/fluentd/{config['new_log_tag']}"
            return f"""
<source>
  @type {config['new_protocol']}
  port {config['new_dst_port']}
  bind {config['new_source_ip']}
  tag {config['new_log_tag']}
  <parse>
    @type json
  </parse>
</source>

<match {config['new_log_tag']}>
  @type http
  endpoint {new_endpoint}
  json_array true
  <format>
    @type json
  </format>
  <buffer>
    flush_interval 10s
  </buffer>
</match>
"""
        except Exception as e:
            logging.error(f"Error generating default configuration: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating default configuration: {str(e)}")