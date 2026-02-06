import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Databricks OAuth
    DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "https://your-workspace.cloud.databricks.com")
    DATABRICKS_SERVER_HOSTNAME = os.getenv("DATABRICKS_SERVER_HOSTNAME", "your-workspace.cloud.databricks.com")
    DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/your-warehouse-id")
    DATABRICKS_CLIENT_ID = os.getenv("DATABRICKS_CLIENT_ID")
    DATABRICKS_CLIENT_SECRET = os.getenv("DATABRICKS_CLIENT_SECRET")
    
    # Unity Catalog
    DATABRICKS_CATALOG = os.getenv("DATABRICKS_CATALOG", "main")
    DATABRICKS_SCHEMA = os.getenv("DATABRICKS_SCHEMA", "default")
    DATABRICKS_VOLUME = os.getenv("DATABRICKS_VOLUME", "csv_uploads")
    
    # File Configuration
    MAX_FILE_SIZE_MB = float(os.getenv("MAX_FILE_SIZE_MB", "10"))
    CSV_COLUMNS_REQUIRED = [col.strip() for col in os.getenv("CSV_COLUMNS_REQUIRED", "t24_customer_code").split(",")]
    
    # OAuth Callback
    OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8501/oauth_callback")
    
    # Streamlit
    STREAMLIT_SERVER_PORT = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    
    # POC Configuration
    POC_DASHBOARD_ID = os.getenv("POC_DASHBOARD_ID", "01ef45fd-8a02-159c-859a-654fac123456")
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        required_fields = [
            "DATABRICKS_CLIENT_ID",
            "DATABRICKS_CLIENT_SECRET",
            "DATABRICKS_SERVER_HOSTNAME",
        ]
        
        missing_fields = [field for field in required_fields if not getattr(cls, field, None)]
        
        if missing_fields:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_fields)}. "
                f"Please set these in .env file"
            )
        
        return True
    
    @classmethod
    def get_volume_path(cls):
        """Get full Unity Catalog Volume path"""
        return f"/Volumes/{cls.DATABRICKS_CATALOG}/{cls.DATABRICKS_SCHEMA}/{cls.DATABRICKS_VOLUME}"


# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    import warnings
    warnings.warn(str(e))
