import subprocess
from fastapi import HTTPException

class DatabaseFluentdDeployment:
    def __init__(self, conf_file_path='/etc/fluent/fluentd.conf'):
        self.conf_file_path = conf_file_path

    async def configure_fluentd(self, config, system, TAG_NAME):
        if config['new_log_tag'] != TAG_NAME:
            raise HTTPException(status_code=400, detail="TAG_NAME과 new_log_tag 값이 동일하여야 합니다.")
        
        if system == 'mysql':
            new_conf_text = self._mysql_conf(config)
        elif system == 'mssql':
            new_conf_text = self._mssql_conf(config)
        else:
            raise HTTPException(status_code=400, detail="Unsupported database system")

        try:
            with open(self.conf_file_path, 'a') as file:
                file.write(new_conf_text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write to the configuration file: {e}")

        try:
            subprocess.run(['sudo', '/bin/systemctl', 'restart', 'fluentd'], check=True)
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"Failed to restart Fluentd service: {e}")

        return {"status": "success", "message": "Fluentd service restarted and configuration updated successfully"}
    
    def _mysql_conf(self, config):
        try:
            new_endpoint = f"http://localhost:8088/collect_log/mysql/{config['new_log_tag']}"
            return f"""
<source>
  @type sql
  @id input_mysql
  adapter mysql # mysql2 로 바꿔야 할 수도
  host {config['host']}
  port 3306
  database {config['database']}
  username {config['user']}
  password {config['password']}
  query SELECT * FROM {config['table_name']} WHERE updated_at > :updated_at
  state_file /var/log/fluent/sql_input_state.json
  tag {config['new_log_tag']}
  table {config['table_name']}
  update_column updated_at
  update_column_type datetime
  run_interval 5m
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
            print("==================")
            print(f"Error generating MySQL configuration: {str(e)}")
            print("==================")
            raise HTTPException(status_code=500, detail=f"Error generating MySQL configuration: {str(e)}")

    def _mssql_conf(self, config):
        try:
            new_endpoint = f"http://localhost:8088/collect_log/mssql/{config['new_log_tag']}"
            return f"""
<source>
  @type sql 
  @id input_mssql
  adapter tinytds 
  host {config['host']}
  port 1433
  database {config['database']}
  username {config['user']}
  password {config['password']}
  query SELECT * FROM {config['table_name']} WHERE updated_at > :updated_at
  state_file /var/log/fluent/sql_input_state.json
  tag {config['new_log_tag']}
  table {config['table_name']}
  update_column updated_at
  update_column_type datetime
  run_interval 5m
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
            print("==================")
            print(f"Error generating MsSQL configuration: {str(e)}")
            print("==================")
            raise HTTPException(status_code=500, detail=f"Error generating MsSQL configuration: {str(e)}")
