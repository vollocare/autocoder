"""
Logging utilities for the Autocoder tool.
"""

import sys
import time
import subprocess
from typing import Optional, List, Dict, Any
from enum import Enum
from colorama import init, Fore, Style

from autocoder.utils.config import config

# Initialize colorama
init(autoreset=True)


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = 0
    INFO = 1
    SUCCESS = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5


class Logger:
    """Logger class for the Autocoder tool."""
    
    def __init__(self):
        self.verbose = config.get("verbose", True)
        self.colors_enabled = config.get("colors_enabled", True)
        self.min_level = LogLevel.DEBUG if self.verbose else LogLevel.INFO
        self.command_history: List[Dict[str, Any]] = []
    
    def set_verbose(self, verbose: bool):
        """Set verbose mode."""
        self.verbose = verbose
        self.min_level = LogLevel.DEBUG if verbose else LogLevel.INFO
    
    def set_colors_enabled(self, enabled: bool):
        """Enable or disable colors."""
        self.colors_enabled = enabled
    
    def _get_color_for_level(self, level: LogLevel) -> str:
        """Get the color for a log level."""
        if not self.colors_enabled:
            return ""
        
        colors = {
            LogLevel.DEBUG: Fore.CYAN,
            LogLevel.INFO: Fore.WHITE,
            LogLevel.SUCCESS: Fore.GREEN,
            LogLevel.WARNING: Fore.YELLOW,
            LogLevel.ERROR: Fore.RED,
            LogLevel.CRITICAL: Fore.RED + Style.BRIGHT
        }
        
        return colors.get(level, "")
    
    def _get_prefix_for_level(self, level: LogLevel) -> str:
        """Get the prefix for a log level."""
        prefixes = {
            LogLevel.DEBUG: "DEBUG",
            LogLevel.INFO: "INFO",
            LogLevel.SUCCESS: "SUCCESS",
            LogLevel.WARNING: "WARNING",
            LogLevel.ERROR: "ERROR",
            LogLevel.CRITICAL: "CRITICAL"
        }
        
        return prefixes.get(level, "")
    
    def log(self, message: str, level: LogLevel = LogLevel.INFO, end: str = "\n"):
        """Log a message with a specific level."""
        if level.value < self.min_level.value:
            return
        
        color = self._get_color_for_level(level)
        prefix = self._get_prefix_for_level(level)
        
        if self.colors_enabled:
            sys.stdout.write(f"{color}[{prefix}] {message}{Style.RESET_ALL}{end}")
        else:
            sys.stdout.write(f"[{prefix}] {message}{end}")
        sys.stdout.flush()
    
    def debug(self, message: str):
        """Log a debug message."""
        self.log(message, LogLevel.DEBUG)
    
    def info(self, message: str):
        """Log an info message."""
        self.log(message, LogLevel.INFO)
    
    def success(self, message: str):
        """Log a success message."""
        self.log(message, LogLevel.SUCCESS)
    
    def warning(self, message: str):
        """Log a warning message."""
        self.log(message, LogLevel.WARNING)
    
    def error(self, message: str):
        """Log an error message."""
        self.log(message, LogLevel.ERROR)
    
    def critical(self, message: str):
        """Log a critical message."""
        self.log(message, LogLevel.CRITICAL)
    
    def progress(self, message: str, current: int, total: int, width: int = 30):
        """Show a progress bar."""
        if not self.verbose:
            return
        
        percentage = min(100, int(100.0 * current / total))
        filled_width = int(width * current / total)
        
        bar = "█" * filled_width + " " * (width - filled_width)
        output = f"\r{message} [{bar}] {percentage}%"
        
        if self.colors_enabled:
            if percentage < 30:
                color = Fore.RED
            elif percentage < 70:
                color = Fore.YELLOW
            else:
                color = Fore.GREEN
            sys.stdout.write(f"{color}{output}{Style.RESET_ALL}")
        else:
            sys.stdout.write(output)
        
        if current >= total:
            sys.stdout.write("\n")
        
        sys.stdout.flush()
    
    def command(self, cmd: str, cwd: Optional[str] = None, shell: bool = True):
        """
        Log and execute a command. Returns the result of the command execution.
        When in verbose mode, logs the command, output, and result.
        """
        start_time = time.time()
        
        # Always log the command that's about to be executed
        self.debug(f"Executing command: {cmd}")
        if cwd:
            self.debug(f"Working directory: {cwd}")
        
        # Record command in history
        cmd_record = {
            "command": cmd,
            "cwd": cwd,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": None,
            "output": None,
            "error": None,
            "duration": None
        }
        
        try:
            # Execute the command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=shell,
                cwd=cwd,
                universal_newlines=True
            )
            
            # Stream output in real-time if in verbose mode
            stdout_lines = []
            stderr_lines = []
            
            # Stream stdout
            for line in process.stdout:
                stdout_lines.append(line)
                if self.verbose:
                    sys.stdout.write(line)
                    sys.stdout.flush()
            
            # Collect stderr
            for line in process.stderr:
                stderr_lines.append(line)
                if self.verbose:
                    color = self._get_color_for_level(LogLevel.ERROR)
                    if self.colors_enabled:
                        sys.stderr.write(f"{color}{line}{Style.RESET_ALL}")
                    else:
                        sys.stderr.write(line)
                    sys.stderr.flush()
            
            # Wait for completion
            process.wait()
            duration = time.time() - start_time
            
            # Update command record
            stdout_content = "".join(stdout_lines)
            stderr_content = "".join(stderr_lines)
            cmd_record["success"] = process.returncode == 0
            cmd_record["output"] = stdout_content
            cmd_record["error"] = stderr_content
            cmd_record["returncode"] = process.returncode
            cmd_record["duration"] = f"{duration:.2f}s"
            
            # Log the result
            if process.returncode == 0:
                self.success(f"Command completed successfully in {duration:.2f}s")
            else:
                self.error(f"Command failed with exit code {process.returncode} in {duration:.2f}s")
                
                # If not verbose mode (didn't already output error), show error
                if not self.verbose and stderr_content:
                    self.error(f"Error output: {stderr_content.strip()}")
            
            # Add to command history
            self.command_history.append(cmd_record)
            
            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout_content,
                "stderr": stderr_content,
                "duration": duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            # Update command record
            cmd_record["success"] = False
            cmd_record["error"] = error_msg
            cmd_record["duration"] = f"{duration:.2f}s"
            
            # Log the error
            self.error(f"Failed to execute command: {error_msg}")
            
            # Add to command history
            self.command_history.append(cmd_record)
            
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": error_msg,
                "duration": duration
            }
    
    def print_command_history(self):
        """Print the history of all commands executed."""
        if not self.command_history:
            self.info("No commands have been executed")
            return
        
        self.info("Command execution history:")
        for i, cmd in enumerate(self.command_history, 1):
            status = "✓" if cmd["success"] else "✗"
            color = Fore.GREEN if cmd["success"] else Fore.RED
            
            if self.colors_enabled:
                sys.stdout.write(f"{color}[{status}] {i}. {cmd['command']} ({cmd['duration']}){Style.RESET_ALL}\n")
            else:
                sys.stdout.write(f"[{status}] {i}. {cmd['command']} ({cmd['duration']})\n")


# Create a singleton instance
logger = Logger() 