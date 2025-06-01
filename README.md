# Oracle 19c PDB Refresh Tool

A GUI application to automate Oracle 19c Database PDB refresh operations from PROD to QA environments.

## Features

- User-friendly graphical interface
- Support for both full database and schema-level refresh
- Secure password handling
- Configuration save/load functionality
- Real-time status updates
- Automated export (expdp) and import (impdp) operations

## Prerequisites

1. Python 3.7 or higher
2. Oracle Client libraries installed
3. SSH access to both source and target servers
4. Oracle Data Pump directory configured on both servers
5. Required Python packages (install using `pip install -r requirements.txt`):
   - cx_Oracle
   - python-dotenv
   - paramiko
   - tkcalendar

## Installation

1. Clone or download this repository
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure Oracle Client libraries are properly installed and configured

## Usage

1. Run the application:
   ```bash
   python oracle_refresh_gui.py
   ```

2. Fill in the required information:
   - Source (PROD) server details
   - Target (QA) server details
   - Select refresh type (Full or Schema)
   - For schema refresh, enter comma-separated schema names

3. Optional: Save your configuration for future use using the "Save Configuration" button

4. Click "Start Refresh" to begin the refresh process

## Configuration

The application supports saving and loading configurations in JSON format. Saved configurations include:
- Server hostnames
- Port numbers
- Service names
- Usernames

Note: Passwords are not saved in the configuration file for security reasons.

## Important Notes

1. Ensure you have proper permissions on both source and target databases
2. The tool uses Oracle Data Pump (expdp/impdp) for refresh operations
3. Make sure the DATA_PUMP_DIR directory is properly configured on both servers
4. For schema-level refresh, enter schema names separated by commas
5. The application requires SSH access to both servers for executing Data Pump commands

## Troubleshooting

Common issues and solutions:

1. Connection errors:
   - Verify hostname, port, and service name
   - Check network connectivity
   - Ensure Oracle Client libraries are properly installed

2. Permission errors:
   - Verify database user privileges
   - Check SSH access permissions
   - Ensure DATA_PUMP_DIR is accessible

3. Data Pump errors:
   - Check available disk space
   - Verify Data Pump directory permissions
   - Review export/import logs in the DATA_PUMP_DIR

## Security Considerations

1. Database passwords are not stored in configuration files
2. All connections use Oracle's secure authentication
3. SSH connections use paramiko's secure implementation
4. Sensitive information is masked in the GUI

## Support

For issues and feature requests, please create an issue in the repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 