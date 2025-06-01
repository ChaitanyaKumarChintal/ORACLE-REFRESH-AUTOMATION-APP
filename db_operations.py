import cx_Oracle
import paramiko
import os
from datetime import datetime
import time

class OracleRefreshOperations:
    def __init__(self, source_details, target_details):
        self.source = source_details
        self.target = target_details
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def connect_to_db(self, details):
        """Establish connection to Oracle database"""
        dsn = cx_Oracle.makedsn(
            details['host'],
            details['port'],
            service_name=details['service']
        )
        return cx_Oracle.connect(
            user=details['user'],
            password=details['password'],
            dsn=dsn
        )
        
    def get_remote_oracle_env(self, host, username, password):
        """Get Oracle environment variables from remote server"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(host, username=username, password=password)
            # Source the profile and print environment variables
            cmd = "source ~/.bash_profile > /dev/null 2>&1 || source ~/.profile > /dev/null 2>&1; env | grep -E 'ORACLE|TNS|PATH'"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            env_output = stdout.read().decode()
            
            # Parse environment variables
            env_vars = {}
            for line in env_output.splitlines():
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
                    
            return env_vars
        finally:
            ssh.close()
            
    def execute_remote_command(self, host, username, password, command):
        """Execute command on remote server using SSH with sourced environment"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(host, username=username, password=password)
            
            # Get Oracle environment
            env_vars = self.get_remote_oracle_env(host, username, password)
            
            # Create the command with sourced environment
            wrapped_command = f"""
            source ~/.bash_profile > /dev/null 2>&1 || source ~/.profile > /dev/null 2>&1
            export ORACLE_HOME="{env_vars.get('ORACLE_HOME', '')}"
            export PATH="{env_vars.get('PATH', '')}"
            export TNS_ADMIN="{env_vars.get('TNS_ADMIN', '')}"
            export LD_LIBRARY_PATH="{env_vars.get('LD_LIBRARY_PATH', '')}"
            {command}
            """
            
            stdin, stdout, stderr = ssh.exec_command(wrapped_command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if error:
                raise Exception(f"Remote command error: {error}")
                
            return output
        finally:
            ssh.close()
            
    def perform_full_refresh(self, dump_dir="/tmp"):
        """Perform full database refresh"""
        dump_file = f"{dump_dir}/full_export_{self.timestamp}.dmp"
        log_file = f"{dump_dir}/full_export_{self.timestamp}.log"
        
        # Get environment variables from source and target servers
        source_env = self.get_remote_oracle_env(
            self.source['host'],
            self.source['user'],
            self.source['password']
        )
        
        target_env = self.get_remote_oracle_env(
            self.target['host'],
            self.target['user'],
            self.target['password']
        )
        
        # Export command using source environment
        expdp_cmd = f"""
        export ORACLE_HOME="{source_env.get('ORACLE_HOME', '')}"
        export PATH="{source_env.get('PATH', '')}"
        export TNS_ADMIN="{source_env.get('TNS_ADMIN', '')}"
        expdp {self.source['user']}/{self.source['password']}@{self.source['service']} \
        FULL=Y \
        DIRECTORY=DATA_PUMP_DIR \
        DUMPFILE=full_export_{self.timestamp}.dmp \
        LOGFILE=full_export_{self.timestamp}.log \
        FLASHBACK_TIME=systimestamp
        """
        
        # Import command using target environment
        impdp_cmd = f"""
        export ORACLE_HOME="{target_env.get('ORACLE_HOME', '')}"
        export PATH="{target_env.get('PATH', '')}"
        export TNS_ADMIN="{target_env.get('TNS_ADMIN', '')}"
        impdp {self.target['user']}/{self.target['password']}@{self.target['service']} \
        FULL=Y \
        DIRECTORY=DATA_PUMP_DIR \
        DUMPFILE=full_export_{self.timestamp}.dmp \
        LOGFILE=import_full_{self.timestamp}.log \
        TABLE_EXISTS_ACTION=REPLACE
        """
        
        try:
            # Execute export with source environment
            self.execute_remote_command(
                self.source['host'],
                self.source['user'],
                self.source['password'],
                expdp_cmd
            )
            
            # Wait for export to complete
            time.sleep(10)
            
            # Execute import with target environment
            self.execute_remote_command(
                self.target['host'],
                self.target['user'],
                self.target['password'],
                impdp_cmd
            )
            
            return True
            
        except Exception as e:
            raise Exception(f"Refresh failed: {str(e)}")
            
    def perform_schema_refresh(self, schemas, dump_dir="/tmp"):
        """Perform schema-level refresh"""
        schema_list = schemas.replace(" ", "")
        dump_file = f"{dump_dir}/schema_export_{self.timestamp}.dmp"
        log_file = f"{dump_dir}/schema_export_{self.timestamp}.log"
        
        # Get environment variables from source and target servers
        source_env = self.get_remote_oracle_env(
            self.source['host'],
            self.source['user'],
            self.source['password']
        )
        
        target_env = self.get_remote_oracle_env(
            self.target['host'],
            self.target['user'],
            self.target['password']
        )
        
        # Export command using source environment
        expdp_cmd = f"""
        export ORACLE_HOME="{source_env.get('ORACLE_HOME', '')}"
        export PATH="{source_env.get('PATH', '')}"
        export TNS_ADMIN="{source_env.get('TNS_ADMIN', '')}"
        expdp {self.source['user']}/{self.source['password']}@{self.source['service']} \
        SCHEMAS={schema_list} \
        DIRECTORY=DATA_PUMP_DIR \
        DUMPFILE=schema_export_{self.timestamp}.dmp \
        LOGFILE=schema_export_{self.timestamp}.log \
        FLASHBACK_TIME=systimestamp
        """
        
        # Import command using target environment
        impdp_cmd = f"""
        export ORACLE_HOME="{target_env.get('ORACLE_HOME', '')}"
        export PATH="{target_env.get('PATH', '')}"
        export TNS_ADMIN="{target_env.get('TNS_ADMIN', '')}"
        impdp {self.target['user']}/{self.target['password']}@{self.target['service']} \
        SCHEMAS={schema_list} \
        DIRECTORY=DATA_PUMP_DIR \
        DUMPFILE=schema_export_{self.timestamp}.dmp \
        LOGFILE=import_schema_{self.timestamp}.log \
        TABLE_EXISTS_ACTION=REPLACE
        """
        
        try:
            # Execute export with source environment
            self.execute_remote_command(
                self.source['host'],
                self.source['user'],
                self.source['password'],
                expdp_cmd
            )
            
            # Wait for export to complete
            time.sleep(10)
            
            # Execute import with target environment
            self.execute_remote_command(
                self.target['host'],
                self.target['user'],
                self.target['password'],
                impdp_cmd
            )
            
            return True
            
        except Exception as e:
            raise Exception(f"Schema refresh failed: {str(e)}")
            
    def verify_connection(self):
        """Verify database connections"""
        try:
            # Test source connection
            source_conn = self.connect_to_db(self.source)
            source_conn.close()
            
            # Test target connection
            target_conn = self.connect_to_db(self.target)
            target_conn.close()
            
            return True
        except Exception as e:
            raise Exception(f"Connection verification failed: {str(e)}") 