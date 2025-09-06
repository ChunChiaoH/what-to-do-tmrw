"""
Logging configuration for What To Do Tomorrow Agent
Supports both local file logging and cloud deployment
"""
import logging
import os
from datetime import datetime

def setup_logging():
    """Setup logging configuration - cloud-compatible"""
    
    # Check if we're running in Streamlit Cloud (no write access to filesystem)
    is_cloud_deployment = (
        os.getenv("STREAMLIT_SHARING") or 
        os.getenv("STREAMLIT_SERVER_HEADLESS") or 
        not os.access(".", os.W_OK)
    )
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if is_cloud_deployment:
        # Cloud deployment: use console logging only
        logging.basicConfig(
            level=logging.WARNING,  # Reduce noise in cloud logs
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]  # Console output only
        )
    else:
        # Local development: use file logging
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
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
    agent_logger.setLevel(logging.WARNING if is_cloud_deployment else logging.INFO)
    
    api_logger = logging.getLogger('api_clients')
    api_logger.setLevel(logging.WARNING if is_cloud_deployment else logging.INFO)
    
    if not is_cloud_deployment:
        # Add file handlers for local development only
        today = datetime.now().strftime("%Y-%m-%d")
        logs_dir = "logs"
        
        agent_handler = logging.FileHandler(f"{logs_dir}/agent_{today}.log")
        agent_handler.setFormatter(detailed_formatter)
        agent_logger.addHandler(agent_handler)
        
        api_handler = logging.FileHandler(f"{logs_dir}/api_{today}.log")
        api_handler.setFormatter(detailed_formatter)
        api_logger.addHandler(api_handler)
    
    return agent_logger, api_logger