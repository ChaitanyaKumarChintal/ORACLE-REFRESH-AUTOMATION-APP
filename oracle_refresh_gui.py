import tkinter as tk
from tkinter import messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.dialogs import Messagebox
import json
import os
import paramiko
from dotenv import load_dotenv
import cx_Oracle
from datetime import datetime
from db_operations import OracleRefreshOperations

class ModernTheme:
    """Modern color scheme and styles"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    LIGHT = "light"
    DARK = "dark"
    
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE_LARGE = 16
    FONT_SIZE_MEDIUM = 12
    FONT_SIZE_SMALL = 10
    
    PADDING = 10
    MARGIN = 15
    
    # Dark mode colors
    DARK_BG = "#1e1e1e"
    DARK_FG = "#ffffff"
    DARK_TERMINAL_BG = "#2b2b2b"
    DARK_TERMINAL_FG = "#e6e6e6"
    
    # Light mode colors
    LIGHT_BG = "#ffffff"
    LIGHT_FG = "#202124"
    LIGHT_TERMINAL_BG = "#f8f9fa"
    LIGHT_TERMINAL_FG = "#202124"
    
class OracleRefreshGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Oracle 19c PDB Refresh Tool")
        self.root.geometry("1200x900")
        
        # Initialize theme state
        self.is_dark_mode = True
        self.current_theme = "darkly" if self.is_dark_mode else "cosmo"
        self.root.style.theme_use(self.current_theme)
        
        # Create main scrolled frame
        self.main_frame = ScrolledFrame(self.root, autohide=True)
        self.main_frame.pack(fill=BOTH, expand=YES, padx=ModernTheme.MARGIN)
        
        # Create header with theme toggle
        self.create_header()
        self.create_source_section()
        self.create_target_section()
        self.create_refresh_section()
        self.create_terminal_section()
        
        # Initialize sessions
        self.source_session = None
        self.target_session = None
        
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.is_dark_mode = not self.is_dark_mode
        new_theme = "darkly" if self.is_dark_mode else "cosmo"
        self.root.style.theme_use(new_theme)
        
        # Update terminal colors
        if self.is_dark_mode:
            self.terminal.configure(
                bg=ModernTheme.DARK_TERMINAL_BG,
                fg=ModernTheme.DARK_TERMINAL_FG,
                insertbackground=ModernTheme.DARK_TERMINAL_FG  # Cursor color
            )
        else:
            self.terminal.configure(
                bg=ModernTheme.LIGHT_TERMINAL_BG,
                fg=ModernTheme.LIGHT_TERMINAL_FG,
                insertbackground=ModernTheme.LIGHT_TERMINAL_FG  # Cursor color
            )
        
        # Update theme button text
        self.theme_button.configure(
            text="🌞 Light Mode" if self.is_dark_mode else "🌙 Dark Mode"
        )
        
        # Update all entry fields' colors
        self.update_entry_colors()
        
    def update_entry_colors(self):
        """Update colors for all entry fields based on theme"""
        entries = [
            self.source_host, self.source_ssh_user, self.source_ssh_password,
            self.source_oracle_user, self.source_oracle_password, self.source_pdb_name,
            self.source_dir_name, self.source_dir_path,
            self.target_host, self.target_ssh_user, self.target_ssh_password,
            self.target_oracle_user, self.target_oracle_password, self.target_pdb_name,
            self.target_dir_name, self.target_dir_path,
            self.schema_entry
        ]
        
        for entry in entries:
            if self.is_dark_mode:
                entry.configure(
                    foreground=ModernTheme.DARK_TERMINAL_FG
                )
            else:
                entry.configure(
                    foreground=ModernTheme.LIGHT_TERMINAL_FG
                )

    def create_header(self):
        """Create header section"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=X, pady=(ModernTheme.MARGIN, ModernTheme.PADDING))
        
        # Create a container for title and theme toggle
        title_container = ttk.Frame(header_frame)
        title_container.pack(fill=X)
        
        # Main title with primary color
        title = ttk.Label(
            title_container,
            text="Oracle 19c PDB Refresh Tool",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_LARGE, "bold"),
            bootstyle=f"{ModernTheme.PRIMARY}"
        )
        title.pack(side=LEFT, fill=X, expand=YES)
        
        # Theme toggle button
        self.theme_button = ttk.Button(
            title_container,
            text="🌞 Light Mode" if self.is_dark_mode else "🌙 Dark Mode",
            command=self.toggle_theme,
            bootstyle=(ModernTheme.SECONDARY, OUTLINE)
        )
        self.theme_button.pack(side=RIGHT, padx=ModernTheme.PADDING)
        
        # Subtitle with secondary color
        subtitle = ttk.Label(
            header_frame,
            text="Manage and automate your Oracle PDB refresh operations",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_SMALL),
            bootstyle=f"{ModernTheme.SECONDARY}"
        )
        subtitle.pack(fill=X, pady=(ModernTheme.PADDING, 0))
        
        # Set initial colors for labels based on theme
        if self.is_dark_mode:
            title.configure(foreground=ModernTheme.DARK_TERMINAL_FG)
            subtitle.configure(foreground=ModernTheme.DARK_TERMINAL_FG)
        else:
            title.configure(foreground=ModernTheme.LIGHT_TERMINAL_FG)
            subtitle.configure(foreground=ModernTheme.LIGHT_TERMINAL_FG)
        
    def create_source_section(self):
        """Create source (PROD) section"""
        source_frame = ttk.Labelframe(
            self.main_frame,
            text="Source (PROD) Configuration",
            padding=ModernTheme.PADDING,
            bootstyle=f"{ModernTheme.PRIMARY}"
        )
        source_frame.pack(fill=X, pady=ModernTheme.PADDING)
        
        # Create two columns
        left_frame = ttk.Frame(source_frame)
        right_frame = ttk.Frame(source_frame)
        left_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, ModernTheme.PADDING))
        right_frame.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # SSH Details (Left Column)
        ssh_header = ttk.Label(
            left_frame,
            text="SSH Configuration",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_MEDIUM, "bold"),
            bootstyle=f"{ModernTheme.PRIMARY}"
        )
        ssh_header.pack(fill=X, pady=(0, ModernTheme.PADDING))
        
        # Initialize source fields with theme-aware colors
        self.source_host = ttk.Entry(left_frame)
        self.source_ssh_user = ttk.Entry(left_frame)
        self.source_ssh_password = ttk.Entry(left_frame, show="*")
        self.source_oracle_user = ttk.Entry(right_frame)
        self.source_oracle_password = ttk.Entry(right_frame, show="*")
        self.source_pdb_name = ttk.Entry(right_frame)
        
        # Function to create styled input fields
        def create_input_field(parent, label_text, entry_widget, is_password=False):
            field_frame = ttk.Frame(parent)
            field_frame.pack(fill=X, pady=(0, ModernTheme.PADDING))
            
            ttk.Label(
                field_frame,
                text=label_text,
                font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_SMALL),
                bootstyle=f"{ModernTheme.SECONDARY}"
            ).pack(fill=X)
            
            if is_password:
                entry_widget.configure(show="*")
            entry_widget.pack(fill=X, pady=(3, 0))
            
            # Set initial colors based on theme
            if self.is_dark_mode:
                entry_widget.configure(
                    foreground=ModernTheme.DARK_TERMINAL_FG
                )
            else:
                entry_widget.configure(
                    foreground=ModernTheme.LIGHT_TERMINAL_FG
                )
            
            return entry_widget
        
        # Create fields with proper colors
        create_input_field(left_frame, "Hostname:", self.source_host)
        create_input_field(left_frame, "Username:", self.source_ssh_user)
        create_input_field(left_frame, "Password:", self.source_ssh_password, True)
        
        # Oracle Details (Right Column)
        oracle_header = ttk.Label(
            right_frame,
            text="Oracle Configuration",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_MEDIUM, "bold"),
            bootstyle=f"{ModernTheme.PRIMARY}"
        )
        oracle_header.pack(fill=X, pady=(0, ModernTheme.PADDING))
        
        # Create Oracle fields with proper colors
        create_input_field(right_frame, "Username:", self.source_oracle_user)
        create_input_field(right_frame, "Password:", self.source_oracle_password, True)
        create_input_field(right_frame, "PDB Name:", self.source_pdb_name)
        
        # Directory Details (Bottom)
        dir_frame = ttk.Frame(source_frame)
        dir_frame.pack(fill=X, pady=(ModernTheme.PADDING, 0))
        
        dir_header = ttk.Label(
            dir_frame,
            text="Directory Configuration",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_MEDIUM, "bold"),
            bootstyle=f"{ModernTheme.PRIMARY}"
        )
        dir_header.pack(fill=X, pady=(0, ModernTheme.PADDING))
        
        # Create a grid for directory inputs
        dir_grid = ttk.Frame(dir_frame)
        dir_grid.pack(fill=X)
        
        # Initialize directory fields with theme-aware colors
        self.source_dir_name = ttk.Entry(dir_grid)
        self.source_dir_path = ttk.Entry(dir_grid)
        
        # Directory Name
        dir_name_frame = ttk.Frame(dir_grid)
        dir_name_frame.pack(side=LEFT, fill=X, expand=YES, padx=(0, ModernTheme.PADDING))
        create_input_field(dir_name_frame, "Directory Name:", self.source_dir_name)
        self.source_dir_name.insert(0, "DATA_PUMP_DIR")
        
        # Physical Path
        dir_path_frame = ttk.Frame(dir_grid)
        dir_path_frame.pack(side=LEFT, fill=X, expand=YES)
        create_input_field(dir_path_frame, "Physical Path:", self.source_dir_path)
        self.source_dir_path.insert(0, "/tmp")
        
        # Test Button with modern styling
        button_frame = ttk.Frame(source_frame)
        button_frame.pack(fill=X, pady=(ModernTheme.PADDING, 0))
        
        test_button = ttk.Button(
            button_frame,
            text="Test PROD Connection",
            command=self.test_source_connection,
            bootstyle=(ModernTheme.INFO, OUTLINE)
        )
        test_button.pack(side=RIGHT)

    def create_target_section(self):
        """Create target (QA) section"""
        target_frame = ttk.Labelframe(
            self.main_frame,
            text="Target (QA) Configuration",
            padding=ModernTheme.PADDING,
            bootstyle=f"{ModernTheme.INFO}"
        )
        target_frame.pack(fill=X, pady=ModernTheme.PADDING)
        
        # Create two columns
        left_frame = ttk.Frame(target_frame)
        right_frame = ttk.Frame(target_frame)
        left_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, ModernTheme.PADDING))
        right_frame.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # SSH Details (Left Column)
        ssh_header = ttk.Label(
            left_frame,
            text="SSH Configuration",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_MEDIUM, "bold"),
            bootstyle=f"{ModernTheme.INFO}"
        )
        ssh_header.pack(fill=X, pady=(0, ModernTheme.PADDING))
        
        # Initialize target fields with theme-aware colors
        self.target_host = ttk.Entry(left_frame)
        self.target_ssh_user = ttk.Entry(left_frame)
        self.target_ssh_password = ttk.Entry(left_frame, show="*")
        self.target_oracle_user = ttk.Entry(right_frame)
        self.target_oracle_password = ttk.Entry(right_frame, show="*")
        self.target_pdb_name = ttk.Entry(right_frame)
        
        # Function to create styled input fields
        def create_input_field(parent, label_text, entry_widget, is_password=False):
            field_frame = ttk.Frame(parent)
            field_frame.pack(fill=X, pady=(0, ModernTheme.PADDING))
            
            ttk.Label(
                field_frame,
                text=label_text,
                font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_SMALL),
                bootstyle=f"{ModernTheme.SECONDARY}"
            ).pack(fill=X)
            
            if is_password:
                entry_widget.configure(show="*")
            entry_widget.pack(fill=X, pady=(3, 0))
            
            # Set initial colors based on theme
            if self.is_dark_mode:
                entry_widget.configure(
                    foreground=ModernTheme.DARK_TERMINAL_FG
                )
            else:
                entry_widget.configure(
                    foreground=ModernTheme.LIGHT_TERMINAL_FG
                )
            
            return entry_widget
        
        # Create fields with proper colors
        create_input_field(left_frame, "Hostname:", self.target_host)
        create_input_field(left_frame, "Username:", self.target_ssh_user)
        create_input_field(left_frame, "Password:", self.target_ssh_password, True)
        
        # Oracle Details (Right Column)
        oracle_header = ttk.Label(
            right_frame,
            text="Oracle Configuration",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_MEDIUM, "bold"),
            bootstyle=f"{ModernTheme.INFO}"
        )
        oracle_header.pack(fill=X, pady=(0, ModernTheme.PADDING))
        
        # Create Oracle fields with proper colors
        create_input_field(right_frame, "Username:", self.target_oracle_user)
        create_input_field(right_frame, "Password:", self.target_oracle_password, True)
        create_input_field(right_frame, "PDB Name:", self.target_pdb_name)
        
        # Directory Details (Bottom)
        dir_frame = ttk.Frame(target_frame)
        dir_frame.pack(fill=X, pady=(ModernTheme.PADDING, 0))
        
        dir_header = ttk.Label(
            dir_frame,
            text="Directory Configuration",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_MEDIUM, "bold"),
            bootstyle=f"{ModernTheme.INFO}"
        )
        dir_header.pack(fill=X, pady=(0, ModernTheme.PADDING))
        
        # Create a grid for directory inputs
        dir_grid = ttk.Frame(dir_frame)
        dir_grid.pack(fill=X)
        
        # Initialize directory fields with theme-aware colors
        self.target_dir_name = ttk.Entry(dir_grid)
        self.target_dir_path = ttk.Entry(dir_grid)
        
        # Directory Name
        dir_name_frame = ttk.Frame(dir_grid)
        dir_name_frame.pack(side=LEFT, fill=X, expand=YES, padx=(0, ModernTheme.PADDING))
        create_input_field(dir_name_frame, "Directory Name:", self.target_dir_name)
        self.target_dir_name.insert(0, "DATA_PUMP_DIR")
        
        # Physical Path
        dir_path_frame = ttk.Frame(dir_grid)
        dir_path_frame.pack(side=LEFT, fill=X, expand=YES)
        create_input_field(dir_path_frame, "Physical Path:", self.target_dir_path)
        self.target_dir_path.insert(0, "/tmp")
        
        # Test Button with modern styling
        button_frame = ttk.Frame(target_frame)
        button_frame.pack(fill=X, pady=(ModernTheme.PADDING, 0))
        
        test_button = ttk.Button(
            button_frame,
            text="Test QA Connection",
            command=self.test_target_connection,
            bootstyle=(ModernTheme.INFO, OUTLINE)
        )
        test_button.pack(side=RIGHT)

    def create_refresh_section(self):
        """Create refresh options section"""
        refresh_frame = ttk.Labelframe(
            self.main_frame,
            text="Refresh Configuration",
            padding=ModernTheme.PADDING,
            bootstyle=f"{ModernTheme.SUCCESS}"
        )
        refresh_frame.pack(fill=X, pady=ModernTheme.PADDING)
        
        # Create a container for the refresh options
        options_frame = ttk.Frame(refresh_frame)
        options_frame.pack(fill=X)
        
        # Refresh Type Selection (Put this first)
        type_frame = ttk.Frame(options_frame)
        type_frame.pack(fill=X, pady=(0, ModernTheme.PADDING))
        
        type_label = ttk.Label(
            type_frame,
            text="Refresh Type",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_MEDIUM, "bold"),
            bootstyle=f"{ModernTheme.SUCCESS}"
        )
        type_label.pack(fill=X, pady=(0, ModernTheme.PADDING))
        
        # Initialize refresh type combobox with theme-aware colors
        self.refresh_type = ttk.Combobox(
            type_frame,
            values=["FULL", "Schema"],
            state="readonly",
            bootstyle=f"{ModernTheme.SUCCESS}"
        )
        self.refresh_type.set("FULL")
        self.refresh_type.pack(side=LEFT)
        
        # Set initial colors for combobox
        if self.is_dark_mode:
            self.refresh_type.configure(
                foreground=ModernTheme.DARK_TERMINAL_FG
            )
        else:
            self.refresh_type.configure(
                foreground=ModernTheme.LIGHT_TERMINAL_FG
            )
        
        self.refresh_type.bind("<<ComboboxSelected>>", self.on_refresh_type_change)
        
        # Schema selection
        schema_frame = ttk.Frame(options_frame)
        schema_frame.pack(fill=X, pady=(0, ModernTheme.PADDING))
        
        schema_label = ttk.Label(
            schema_frame,
            text="Schema Selection",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_MEDIUM, "bold"),
            bootstyle=f"{ModernTheme.SUCCESS}"
        )
        schema_label.pack(fill=X, pady=(0, ModernTheme.PADDING))
        
        schema_entry_frame = ttk.Frame(schema_frame)
        schema_entry_frame.pack(fill=X)
        
        schema_desc_label = ttk.Label(
            schema_entry_frame,
            text="Enter schema names (comma-separated):",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_SMALL),
            bootstyle=f"{ModernTheme.SECONDARY}"
        )
        schema_desc_label.pack(side=LEFT, padx=(0, ModernTheme.PADDING))
        
        # Initialize schema entry with theme-aware colors
        self.schema_entry = ttk.Entry(schema_entry_frame)
        self.schema_entry.pack(side=LEFT, fill=X, expand=YES)
        
        # Set initial colors for schema entry
        if self.is_dark_mode:
            self.schema_entry.configure(
                foreground=ModernTheme.DARK_TERMINAL_FG
            )
        else:
            self.schema_entry.configure(
                foreground=ModernTheme.LIGHT_TERMINAL_FG
            )
        
        # Initially disable schema entry if FULL is selected
        if self.refresh_type.get() == "FULL":
            self.schema_entry.configure(state="disabled")
        
        # Action Buttons
        button_frame = ttk.Frame(refresh_frame)
        button_frame.pack(fill=X, pady=(ModernTheme.PADDING, 0))
        
        # Save Config Button
        save_button = ttk.Button(
            button_frame,
            text="Save Configuration",
            command=self.save_config,
            bootstyle=(ModernTheme.SECONDARY, OUTLINE)
        )
        save_button.pack(side=LEFT, padx=(0, ModernTheme.PADDING))
        
        # Load Config Button
        load_button = ttk.Button(
            button_frame,
            text="Load Configuration",
            command=self.load_config,
            bootstyle=(ModernTheme.SECONDARY, OUTLINE)
        )
        load_button.pack(side=LEFT)
        
        # Start Refresh Button
        start_button = ttk.Button(
            button_frame,
            text="Start Refresh",
            command=self.start_refresh,
            bootstyle=ModernTheme.SUCCESS
        )
        start_button.pack(side=RIGHT)

    def create_terminal_section(self):
        """Create terminal output section"""
        terminal_frame = ttk.Labelframe(
            self.main_frame,
            text="Operation Log",
            padding=ModernTheme.PADDING,
            bootstyle=ModernTheme.DARK
        )
        terminal_frame.pack(fill=BOTH, expand=YES, pady=(ModernTheme.PADDING, ModernTheme.MARGIN))
        
        # Create the terminal output area with dark mode styling
        self.terminal = scrolledtext.ScrolledText(
            terminal_frame,
            wrap=tk.WORD,
            height=15,
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_SMALL),
            bg=ModernTheme.DARK_TERMINAL_BG if self.is_dark_mode else ModernTheme.LIGHT_TERMINAL_BG,
            fg=ModernTheme.DARK_TERMINAL_FG if self.is_dark_mode else ModernTheme.LIGHT_TERMINAL_FG,
            padx=ModernTheme.PADDING,
            pady=ModernTheme.PADDING
        )
        self.terminal.pack(fill=BOTH, expand=YES, pady=ModernTheme.PADDING)
        
        # Configure tag for success messages
        self.terminal.tag_configure(
            "success",
            foreground="#50fa7b" if self.is_dark_mode else "#28a745",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_SMALL, "bold")
        )
        
        # Configure tag for error messages
        self.terminal.tag_configure(
            "error",
            foreground="#ff5555" if self.is_dark_mode else "#dc3545",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_SMALL, "bold")
        )

    def log_message(self, message):
        """Add message to terminal output with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.terminal.insert(tk.END, f"{timestamp} - ", "timestamp")
        self.terminal.insert(tk.END, f"{message}\n")
        self.terminal.see(tk.END)
        self.root.update()
        
    def test_source_connection(self):
        """Test SSH connection to source server"""
        try:
            self.log_message("Testing PROD server connection...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.source_host.get(),
                username=self.source_ssh_user.get(),
                password=self.source_ssh_password.get()
            )
            self.source_session = ssh
            self.log_message("PROD server connection successful!")
            
            # Test .bash_profile sourcing
            self.log_message("Sourcing PROD server .bash_profile...")
            stdin, stdout, stderr = ssh.exec_command("source ~/.bash_profile > /dev/null 2>&1 || source ~/.profile > /dev/null 2>&1; env | grep ORACLE")
            env_output = stdout.read().decode()
            if env_output:
                self.log_message("PROD Oracle environment loaded successfully")
            else:
                self.log_message("Warning: No Oracle environment variables found in PROD")
                
        except Exception as e:
            self.log_message(f"Error connecting to PROD: {str(e)}")
            messagebox.showerror("Connection Error", f"Failed to connect to PROD server: {str(e)}")
            
    def test_target_connection(self):
        """Test SSH connection to target server"""
        try:
            self.log_message("Testing QA server connection...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.target_host.get(),
                username=self.target_ssh_user.get(),
                password=self.target_ssh_password.get()
            )
            self.target_session = ssh
            self.log_message("QA server connection successful!")
            
            # Test .bash_profile sourcing
            self.log_message("Sourcing QA server .bash_profile...")
            stdin, stdout, stderr = ssh.exec_command("source ~/.bash_profile > /dev/null 2>&1 || source ~/.profile > /dev/null 2>&1; env | grep ORACLE")
            env_output = stdout.read().decode()
            if env_output:
                self.log_message("QA Oracle environment loaded successfully")
            else:
                self.log_message("Warning: No Oracle environment variables found in QA")
                
        except Exception as e:
            self.log_message(f"Error connecting to QA: {str(e)}")
            messagebox.showerror("Connection Error", f"Failed to connect to QA server: {str(e)}")
            
    def execute_remote_command(self, session, command, server_type=""):
        """Execute command and show output in terminal"""
        if not session:
            raise Exception(f"No active {server_type} session")
            
        self.log_message(f"Executing on {server_type}:\n{command}\n")
        stdin, stdout, stderr = session.exec_command(command)
        
        # Show output in real-time
        while True:
            line = stdout.readline()
            if not line:
                break
            self.log_message(f"{server_type} > {line.strip()}")
            
        error = stderr.read().decode()
        if error:
            self.log_message(f"{server_type} ERROR > {error}")
            raise Exception(f"{server_type} command error: {error}")
            
    def backup_schema_grants(self, schema):
        """Backup roles, grants, and tablespace settings for a schema"""
        try:
            self.log_message(f"\n=== Backing up grants for schema {schema} ===")
            backup_cmd = f"""
            source ~/.bash_profile > /dev/null 2>&1 || source ~/.profile > /dev/null 2>&1
            
            sqlplus -s {self.target_oracle_user.get()}/{self.target_oracle_password.get()}@{self.target_pdb_name.get()} << 'ENDOFSQL'
            SET PAGESIZE 0 FEEDBACK OFF VERIFY OFF HEADING OFF ECHO OFF
            SPOOL {self.target_dir_path.get()}/qa_{schema}_grants_$(date +%Y%m%d_%H%M%S).sql

            -- Capture roles and admin options
            SELECT 'GRANT '||granted_role||' TO {schema}'||
                   CASE WHEN admin_option='YES' THEN ' WITH ADMIN OPTION;' ELSE ';' END 
            FROM dba_role_privs WHERE grantee = UPPER('{schema}');

            -- Capture system privileges
            SELECT 'GRANT '||privilege||' TO {schema}'||
                   CASE WHEN admin_option='YES' THEN ' WITH ADMIN OPTION;' ELSE ';' END 
            FROM dba_sys_privs WHERE grantee = UPPER('{schema}');

            -- Capture object privileges
            SELECT 'GRANT '||privilege||' ON '||owner||'.'||table_name||' TO {schema}'||
                   CASE WHEN grantable='YES' THEN ' WITH GRANT OPTION;' ELSE ';' END 
            FROM dba_tab_privs WHERE grantee = UPPER('{schema}');

            -- Capture tablespace settings
            SELECT 'ALTER USER {schema} DEFAULT TABLESPACE '||default_tablespace||
                   ' TEMPORARY TABLESPACE '||temporary_tablespace||';'
            FROM dba_users WHERE username = UPPER('{schema}');

            SELECT 'ALTER USER {schema} QUOTA '||
                   CASE WHEN max_bytes=-1 THEN 'UNLIMITED' 
                        ELSE TO_CHAR(ROUND(max_bytes/1024/1024))||'M' END||
                   ' ON '||tablespace_name||';'
            FROM dba_ts_quotas WHERE username = UPPER('{schema}');

            SPOOL OFF
            EXIT;
ENDOFSQL
            """
            self.execute_remote_command(self.target_session, backup_cmd, "QA")
            
        except Exception as e:
            self.log_message(f"Warning: Error backing up grants for {schema}: {str(e)}")
            self.log_message("Continuing with refresh operation...")

    def clean_schema(self, schema):
        """Clean schema by dropping all objects"""
        try:
            self.log_message(f"\n=== Cleaning schema {schema} ===")
            clean_cmd = f"""
            source ~/.bash_profile > /dev/null 2>&1 || source ~/.profile > /dev/null 2>&1
            
            sqlplus -s {self.target_oracle_user.get()}/{self.target_oracle_password.get()}@{self.target_pdb_name.get()} << 'ENDOFSQL'
            SET SERVEROUTPUT ON
            BEGIN
                -- Drop all tables with cascade constraints
                FOR t IN (SELECT table_name FROM dba_tables WHERE owner = UPPER('{schema}')) LOOP
                    BEGIN
                        EXECUTE IMMEDIATE 'DROP TABLE {schema}.'||t.table_name||' CASCADE CONSTRAINTS PURGE';
                    EXCEPTION WHEN OTHERS THEN NULL; END;
                END LOOP;

                -- Drop other objects (sequences, views, procedures, etc.)
                FOR o IN (SELECT object_name, object_type 
                         FROM dba_objects 
                         WHERE owner = UPPER('{schema}')
                         AND object_type NOT IN ('TABLE','INDEX','TABLE PARTITION','INDEX PARTITION')) LOOP
                    BEGIN
                        EXECUTE IMMEDIATE 'DROP '||o.object_type||' {schema}.'||o.object_name||
                                        CASE o.object_type WHEN 'TYPE' THEN ' FORCE' ELSE '' END;
                    EXCEPTION WHEN OTHERS THEN NULL; END;
                END LOOP;

                -- Purge recyclebin
                EXECUTE IMMEDIATE 'PURGE RECYCLEBIN';
            END;
/
            EXIT;
ENDOFSQL
            """
            self.execute_remote_command(self.target_session, clean_cmd, "QA")
            
        except Exception as e:
            self.log_message(f"Error cleaning schema {schema}: {str(e)}")
            raise

    def restore_schema_grants(self, schema, timestamp):
        """Restore previously backed up grants"""
        try:
            self.log_message(f"\n=== Restoring grants for schema {schema} ===")
            restore_cmd = f"""
            source ~/.bash_profile > /dev/null 2>&1 || source ~/.profile > /dev/null 2>&1
            
            sqlplus -s {self.target_oracle_user.get()}/{self.target_oracle_password.get()}@{self.target_pdb_name.get()} << 'ENDOFSQL'
            @{self.target_dir_path.get()}/qa_{schema}_grants_{timestamp}.sql
            EXIT;
ENDOFSQL
            """
            self.execute_remote_command(self.target_session, restore_cmd, "QA")
            
        except Exception as e:
            self.log_message(f"Warning: Error restoring grants for {schema}: {str(e)}")
            self.log_message("Continuing with refresh operation...")

    def post_refresh_tasks(self, schemas):
        """Perform post-refresh tasks: recompile invalid objects and gather statistics"""
        try:
            self.log_message("\n=== Performing post-refresh tasks ===")
            schema_list = ",".join(f"'{schema.strip().upper()}'" for schema in schemas.split(","))
            post_cmd = f"""
            source ~/.bash_profile > /dev/null 2>&1 || source ~/.profile > /dev/null 2>&1
            
            sqlplus -s {self.target_oracle_user.get()}/{self.target_oracle_password.get()}@{self.target_pdb_name.get()} << 'ENDOFSQL'
            SET SERVEROUTPUT ON

            -- Recompile invalid objects
            BEGIN
                FOR obj IN (
                    SELECT owner, object_name, object_type 
                    FROM dba_objects 
                    WHERE status = 'INVALID' 
                    AND owner IN ({schema_list})
                ) LOOP
                    BEGIN
                        EXECUTE IMMEDIATE 'ALTER '||obj.object_type||' '||obj.owner||'.'||obj.object_name||
                                        CASE WHEN obj.object_type='PACKAGE BODY' 
                                             THEN ' COMPILE BODY' 
                                             ELSE ' COMPILE' 
                                        END;
                    EXCEPTION WHEN OTHERS THEN NULL; END;
                END LOOP;
            END;
/

            -- Gather schema statistics
            BEGIN
                FOR user_rec IN (
                    SELECT username 
                    FROM dba_users 
                    WHERE username IN ({schema_list})
                ) LOOP
                    DBMS_STATS.GATHER_SCHEMA_STATS(
                        ownname => user_rec.username,
                        options => 'GATHER AUTO',
                        degree => DBMS_STATS.AUTO_DEGREE
                    );
                END LOOP;
            END;
/

            EXIT;
ENDOFSQL
            """
            self.execute_remote_command(self.target_session, post_cmd, "QA")
            self.log_message("Post-refresh tasks completed successfully")
            
        except Exception as e:
            self.log_message(f"Warning: Error in post-refresh tasks: {str(e)}")
            self.log_message("Continuing with completion...")

    def copy_dumpfile(self, dump_file):
        """Copy dump file using expect script to handle interactive password prompts"""
        try:
            self.log_message("\n=== Copying dump file from PROD to QA using expect ===")
            
            # Create and execute expect script for file transfer
            prod_copy_cmd = f"""
            source ~/.bash_profile > /dev/null 2>&1 || source ~/.profile > /dev/null 2>&1
            cd {self.source_dir_path.get()}
            chmod 644 {dump_file}
            
            # Create expect script
            cat << 'EOF' > /tmp/transfer.exp
#!/usr/bin/expect -f
set timeout -1

# Get arguments
set src_file [lindex $argv 0]
set target_user [lindex $argv 1]
set target_host [lindex $argv 2]
set target_path [lindex $argv 3]
set password [lindex $argv 4]

# Start scp
spawn scp $src_file $target_user@$target_host:$target_path

# Handle password prompt
expect {{
    "yes/no" {{ send "yes\r"; exp_continue }}
    "password:" {{ send "$password\r" }}
}}

# Wait for completion
expect eof
EOF

            # Make expect script executable
            chmod +x /tmp/transfer.exp
            
            # Run expect script
            /tmp/transfer.exp "{dump_file}" "{self.target_ssh_user.get()}" "{self.target_host.get()}" "{self.target_dir_path.get()}" "{self.target_ssh_password.get()}"
            
            # Clean up
            rm -f /tmp/transfer.exp
            """
            self.execute_remote_command(self.source_session, prod_copy_cmd, "PROD")
            
            # Set permissions on target
            qa_chmod_cmd = f"""
            source ~/.bash_profile > /dev/null 2>&1 || source ~/.profile > /dev/null 2>&1
            chmod 644 {self.target_dir_path.get()}/{dump_file}
            """
            self.execute_remote_command(self.target_session, qa_chmod_cmd, "QA")
            
            self.log_message("Dump file transfer completed successfully")
            
        except Exception as e:
            self.log_message(f"Error copying dump file: {str(e)}")
            raise

    def is_operation_successful(self, error_msg, operation_type=""):
        """Check if an operation was actually successful despite error popup"""
        error_msg = error_msg.lower()
        
        # Common success indicators
        success_indicators = [
            "successfully completed",
            "successfully loaded/unloaded",
            "job", "successfully",
            "master table", "successfully"
        ]
        
        # Import-specific indicators
        if operation_type.lower() == "import":
            success_indicators.extend([
                "processing object type",
                "imported",
                "completed at"
            ])
        # Export-specific indicators
        elif operation_type.lower() == "export":
            success_indicators.extend([
                "dump file set",
                "exported",
                "completed at"
            ])
            
        return any(indicator in error_msg for indicator in success_indicators)

    def start_refresh(self):
        """Start the refresh process"""
        try:
            if not self.source_session or not self.target_session:
                raise Exception("Please test both PROD and QA connections first")
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dump_file = f"refresh_{timestamp}.dmp"
            
            # Export from PROD
            self.log_message("\n=== Starting Export from PROD ===")
            export_cmd = f"""
            source ~/.bash_profile > /dev/null 2>&1 || source ~/.profile > /dev/null 2>&1
            cd {self.source_dir_path.get()}
            expdp {self.source_oracle_user.get()}/{self.source_oracle_password.get()}@{self.source_pdb_name.get()} \
            directory={self.source_dir_name.get()} \
            dumpfile={dump_file} \
            logfile=export_{timestamp}.log \
            parallel=2 """
            
            if self.refresh_type.get() == "Schema":
                schemas = self.schema_entry.get()
                if not schemas:
                    raise Exception("Please specify schema names")
                export_cmd += f"schemas={schemas} "
            else:
                export_cmd += "full=y "
                
            try:
                self.execute_remote_command(self.source_session, export_cmd, "PROD")
            except Exception as e:
                if self.is_operation_successful(str(e), "export"):
                    self.log_message("Export completed successfully (ignore error popup)")
                else:
                    raise Exception(f"Export failed: {str(e)}")

            # Continue with the rest of the refresh process...
            self.log_message("\n=== Export completed, proceeding with file transfer ===")
            
            # Copy dump file from PROD to QA
            self.copy_dumpfile(dump_file)
            
            if self.refresh_type.get() == "Schema":
                schemas = self.schema_entry.get().split(",")
                
                # Backup grants for each schema
                for schema in schemas:
                    schema = schema.strip()
                    self.backup_schema_grants(schema)
                
                # Clean each schema
                for schema in schemas:
                    schema = schema.strip()
                    self.clean_schema(schema)
            
            # Import to QA
            self.log_message("\n=== Starting Import to QA ===")
            import_cmd = f"""
            source ~/.bash_profile > /dev/null 2>&1 || source ~/.profile > /dev/null 2>&1
            cd {self.target_dir_path.get()}
            impdp {self.target_oracle_user.get()}/{self.target_oracle_password.get()}@{self.target_pdb_name.get()} \
            directory={self.target_dir_name.get()} \
            dumpfile={dump_file} \
            logfile=import_{timestamp}.log \
            parallel=2 \
            table_exists_action=replace \
            transform=oid:n \
            exclude=user,role_grant,default_role,tablespace_quota """
            
            if self.refresh_type.get() == "Schema":
                schemas = self.schema_entry.get()
                import_cmd += f"schemas={schemas} "
            else:
                import_cmd += "full=y "
            
            try:
                self.execute_remote_command(self.target_session, import_cmd, "QA")
            except Exception as e:
                if self.is_operation_successful(str(e), "import"):
                    self.log_message("Import completed successfully (ignore error popup)")
                else:
                    raise Exception(f"Import failed: {str(e)}")
            
            # Restore grants and perform post-refresh tasks for schema refresh
            if self.refresh_type.get() == "Schema":
                schemas = self.schema_entry.get().split(",")
                for schema in schemas:
                    schema = schema.strip()
                    self.restore_schema_grants(schema, timestamp)
                
                self.post_refresh_tasks(self.schema_entry.get())
            
            self.log_message("\n=== Refresh completed successfully! ===")
            messagebox.showinfo("Success", "Database refresh completed successfully!")
            
        except Exception as e:
            self.log_message(f"\nERROR: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def on_refresh_type_change(self, event):
        """Handle refresh type change"""
        if self.refresh_type.get() == "Schema":
            self.schema_entry.configure(state="normal")
        else:
            self.schema_entry.configure(state="disabled")
            self.schema_entry.delete(0, tk.END)
            
    def save_config(self):
        config = {
            'source': {
                'host': self.source_host.get(),
                'ssh_user': self.source_ssh_user.get(),
                'oracle_user': self.source_oracle_user.get(),
                'pdb_name': self.source_pdb_name.get(),
                'dir_name': self.source_dir_name.get(),
                'dir_path': self.source_dir_path.get()
            },
            'target': {
                'host': self.target_host.get(),
                'ssh_user': self.target_ssh_user.get(),
                'oracle_user': self.target_oracle_user.get(),
                'pdb_name': self.target_pdb_name.get(),
                'dir_name': self.target_dir_name.get(),
                'dir_path': self.target_dir_path.get()
            }
        }
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        self.log_message("Configuration saved successfully!")
        
    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                
            # Clear and load source fields
            self.source_host.delete(0, tk.END)
            self.source_ssh_user.delete(0, tk.END)
            self.source_oracle_user.delete(0, tk.END)
            self.source_pdb_name.delete(0, tk.END)
            self.source_dir_name.delete(0, tk.END)
            self.source_dir_path.delete(0, tk.END)
            
            self.source_host.insert(0, config['source']['host'])
            self.source_ssh_user.insert(0, config['source']['ssh_user'])
            self.source_oracle_user.insert(0, config['source']['oracle_user'])
            self.source_pdb_name.insert(0, config['source']['pdb_name'])
            self.source_dir_name.insert(0, config['source']['dir_name'])
            self.source_dir_path.insert(0, config['source']['dir_path'])
            
            # Clear and load target fields
            self.target_host.delete(0, tk.END)
            self.target_ssh_user.delete(0, tk.END)
            self.target_oracle_user.delete(0, tk.END)
            self.target_pdb_name.delete(0, tk.END)
            self.target_dir_name.delete(0, tk.END)
            self.target_dir_path.delete(0, tk.END)
            
            self.target_host.insert(0, config['target']['host'])
            self.target_ssh_user.insert(0, config['target']['ssh_user'])
            self.target_oracle_user.insert(0, config['target']['oracle_user'])
            self.target_pdb_name.insert(0, config['target']['pdb_name'])
            self.target_dir_name.insert(0, config['target']['dir_name'])
            self.target_dir_path.insert(0, config['target']['dir_path'])
            
            self.log_message("Configuration loaded successfully!")
        except FileNotFoundError:
            self.log_message("Error: Configuration file not found!")
            messagebox.showerror("Error", "Configuration file not found!")

if __name__ == "__main__":
    root = ttk.Window(themename="darkly")  # Start with dark theme by default
    app = OracleRefreshGUI(root)
    root.mainloop() 