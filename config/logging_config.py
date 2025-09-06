"""
Logging configuration for What To Do Tomorrow Agent
"""
import logging
import os
from datetime import datetime

def setup_logging():
    """Setup logging configuration with separate log files"""
    
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Get today's date for log file names
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"{logs_dir}/agent_{today}.log"),
            logging.FileHandler(f"{logs_dir}/debug_{today}.log")
        ]
    )
    
    # Create specific loggers
    agent_logger = logging.getLogger('agent')
    agent_logger.setLevel(logging.INFO)
    
    api_logger = logging.getLogger('api_clients')
    api_logger.setLevel(logging.INFO)
    
    # Add file handlers
    agent_handler = logging.FileHandler(f"{logs_dir}/agent_{today}.log")
    agent_handler.setFormatter(detailed_formatter)
    agent_logger.addHandler(agent_handler)
    
    api_handler = logging.FileHandler(f"{logs_dir}/api_{today}.log")
    api_handler.setFormatter(detailed_formatter)
    api_logger.addHandler(api_handler)
    
    return agent_logger, api_logger