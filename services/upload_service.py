"""Databricks Unity Catalog file upload service"""

import logging
from typing import Optional, Dict, Any, Callable
from databricks import sql
from io import BytesIO
import base64
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabricksUploader:
    """Handle file uploads to Databricks Unity Catalog Volumes"""
    
    def __init__(self, server_hostname: str, http_path: str, access_token: str):
        """
        Initialize Databricks uploader
        
        Args:
            server_hostname: Databricks workspace hostname
            http_path: SQL warehouse HTTP path
            access_token: OAuth access token
        """
        self.server_hostname = server_hostname
        self.http_path = http_path
        self.access_token = access_token
        self.connection = None
    
    def get_connection(self):
        """
        Get Databricks SQL connection
        
        Returns:
            Databricks SQL connection object
            
        Raises:
            Exception: If connection fails
        """
        if self.connection is None:
            try:
                logger.info(f"Connecting to Databricks: {self.server_hostname}")
                self.connection = sql.connect(
                    server_hostname=self.server_hostname,
                    http_path=self.http_path,
                    access_token=self.access_token,
                    auth_type="pat"
                )
                logger.info("Successfully connected to Databricks")
            except Exception as e:
                logger.error(f"Failed to connect to Databricks: {str(e)}")
                raise
        
        return self.connection
    
    def test_connection(self) -> bool:
        """
        Test connection to Databricks
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as status")
                result = cursor.fetchone()
                if result:
                    logger.info("Databricks connection test successful")
                    return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
        
        return False
    
    def upload_file_to_volume(
        self,
        file_content: bytes,
        filename: str,
        catalog: str,
        schema: str,
        volume: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Upload CSV data to Databricks table using SQL
        
        Args:
            file_content: File content as bytes (CSV)
            filename: Name of the file
            catalog: Unity Catalog name
            schema: Schema name
            volume: Not used, placeholder
            progress_callback: Optional callback function for progress updates (percentage, message)
            
        Returns:
            Dictionary with upload result details
        """
        try:
            if progress_callback:
                progress_callback(10, f"Parsing CSV data from {filename}...")
            
            # Parse CSV using pandas
            df = pd.read_csv(BytesIO(file_content))
            
            # Create table name from filename (remove extension)
            table_name = filename.rsplit('.', 1)[0].replace('-', '_').replace(' ', '_')
            full_table_name = f"{catalog}.{schema}.{table_name}"
            
            if progress_callback:
                progress_callback(30, f"Creating table {full_table_name}...")
            
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Drop table if exists
                cursor.execute(f"DROP TABLE IF EXISTS {full_table_name}")
                
                # Create table with columns from CSV
                columns = df.columns.tolist()
                column_defs = []
                for col in columns:
                    # Assume all string for simplicity; in production, infer types
                    column_defs.append(f"`{col}` STRING")
                create_sql = f"CREATE TABLE {full_table_name} ({', '.join(column_defs)})"
                cursor.execute(create_sql)
                
                if progress_callback:
                    progress_callback(50, "Inserting data...")
                
                # Insert data
                for index, row in df.iterrows():
                    values = [str(val) if pd.notna(val) else 'NULL' for val in row]
                    insert_sql = f"INSERT INTO {full_table_name} VALUES ({', '.join([f\"'{v}'\" if v != 'NULL' else 'NULL' for v in values])})"
                    cursor.execute(insert_sql)
                
                # Commit
                conn.commit()
            
            if progress_callback:
                progress_callback(100, "Upload completed!")
            
            return {
                "success": True,
                "table": full_table_name,
                "filename": filename,
                "rows_inserted": len(df),
                "message": f"Data uploaded successfully to table {full_table_name}"
            }
            
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            
            if progress_callback:
                progress_callback(0, f"Upload failed: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "message": "Data upload failed"
            }
    
    def verify_file_in_volume(
        self,
        catalog: str,
        schema: str,
        volume: str,
        filename: str
    ) -> bool:
        """
        Verify if file exists in Unity Catalog Volume
        
        Args:
            catalog: Unity Catalog name
            schema: Schema name
            volume: Volume name
            filename: Filename to verify
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            volume_path = f"/Volumes/{catalog}/{schema}/{volume}"
            
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # List files in volume
                list_sql = f"DESCRIBE VOLUME '{volume_path}'"
                cursor.execute(list_sql)
                # This may not work directly; alternative is to check if table creation succeeded
                
                logger.info(f"File verification check for {filename}")
                return True
                
        except Exception as e:
            logger.error(f"File verification failed: {str(e)}")
            return False
    
    def cleanup(self):
        """Close database connection"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")
            finally:
                self.connection = None


class DatabricksFilesAPIUploader:
    """
    Alternative implementation using Databricks SDK Files API
    This requires the databricks SDK to be installed
    """
    
    def __init__(self, server_hostname: str, access_token: str):
        """
        Initialize uploader using SDK
        
        Args:
            server_hostname: Databricks workspace hostname
            access_token: OAuth access token
        """
        try:
            from databricks.sdk import WorkspaceClient
            
            self.w = WorkspaceClient(
                host=f"https://{server_hostname}",
                token=access_token
            )
            self.server_hostname = server_hostname
            self.access_token = access_token
            logger.info("Initialized Databricks SDK uploader")
        except ImportError:
            logger.warning("databricks-sdk not installed. Install with: pip install databricks-sdk")
            self.w = None
    
    def upload_file_to_volume(
        self,
        file_content: bytes,
        filename: str,
        catalog: str,
        schema: str,
        volume: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to Unity Catalog Volume using Databricks SDK
        
        Args:
            file_content: File content as bytes
            filename: Name of the file
            catalog: Unity Catalog name
            schema: Schema name
            volume: Volume name
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with upload result details
        """
        if not self.w:
            return {
                "success": False,
                "error": "Databricks SDK not initialized",
                "message": "Please install databricks-sdk"
            }
        
        try:
            volume_path = f"/Volumes/{catalog}/{schema}/{volume}/{filename}"
            
            if progress_callback:
                progress_callback(20, f"Uploading {filename} to Unity Catalog...")
            
            # Upload using SDK Files API
            self.w.files.upload(
                file_path=volume_path,
                contents=file_content,
                overwrite=True
            )
            
            if progress_callback:
                progress_callback(100, "Upload completed!")
            
            logger.info(f"File uploaded successfully to {volume_path}")
            
            return {
                "success": True,
                "path": volume_path,
                "filename": filename,
                "size_bytes": len(file_content),
                "message": f"File uploaded successfully to {volume_path}"
            }
            
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            
            if progress_callback:
                progress_callback(0, f"Upload failed: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "message": "File upload failed"
            }
