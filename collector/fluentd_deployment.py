import logging
import subprocess
from fastapi import HTTPException

conf_file_path = '/etc/fluent/fluentd.conf'

async def configure_fluentd(config):
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
        with open(conf_file_path, 'a') as file:
            file.write(new_conf_text)
    except Exception as e:
        logging.error(f"Failed to write to the configuration file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to write to the configuration file: {e}")
    
    try:
        subprocess.run(['/usr/bin/sudo', '/bin/systemctl', 'restart', 'fluentd'], check=True)
        return {"status": "success", "message": "Fluentd service restarted and configuration added successfully"}
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to restart Fluentd service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart Fluentd service: {e}")

