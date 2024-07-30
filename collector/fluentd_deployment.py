import subprocess
import logging
from fastapi import HTTPException

class FluentdDeployment:
    def __init__(self, conf_file_path='/etc/fluent/fluentd.conf'):  
        self.conf_file_path = conf_file_path

    async def configure_fluentd(self, config, TAG_NAME):
        # TAG_NAME과 new_log_tag 값은 동일하여야 함
        if config['new_log_tag'] != TAG_NAME:
            raise HTTPException(status_code=400, detail="TAG_NAME과 new_log_tag 값이 동일하여야 합니다.")

        new_endpoint = f"http://localhost:8088/{config['new_log_tag']}" 
        new_conf_text = f"""
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
    
# genian 버전 conf 파일 
# genian_new_endpoint {collect_log/genian/new_log_tag} 

"""
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
    log_id ${record["logid"]}
    timestamp ${record["timestamp"]}
    log_level ${record["loglevel"]}
    ip ${record["ip"]}
    mac ${record["mac"]}
    fullmsg ${record["fullmsg"]}
    message ${record["message"]}
  </record>
</filter>

<match {config['new_log_tag']}>
  @type http
  endpoint {genian_new_endpoint}
  json_array true
  <format>
    @type json
  </format>
  <buffer>
    flush_interval 10s
  </buffer>
</match>
"""


# fortigate 버전 conf 파일
# fortigate_new_endpoint {collect_log/fortigate/new_log_tag} 
"""
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
  endpoint {fortigate_new_endpoint}
  json_array true
  <format>
    @type json
  </format>
  <buffer>
    flush_interval 10s
  </buffer>
</match>
"""
