"""CSV file validation module"""

import pandas as pd
import io
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVValidator:
    """Validate CSV files for required columns and data integrity"""
    
    def __init__(self, required_columns: List[str], max_size_mb: float = 10.0):
        """
        Initialize CSV validator
        
        Args:
            required_columns: List of required column names
            max_size_mb: Maximum allowed file size in MB
        """
        self.required_columns = [col.lower().strip() for col in required_columns]
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
    
    def validate_file_size(self, file_size_bytes: int) -> Tuple[bool, str]:
        """
        Validate file size
        
        Args:
            file_size_bytes: Size of file in bytes
            
        Returns:
            Tuple of (is_valid, message)
        """
        if file_size_bytes > self.max_size_bytes:
            file_size_mb = file_size_bytes / (1024 * 1024)
            message = f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({self.max_size_mb} MB)"
            logger.warning(message)
            return False, message
        
        file_size_mb = file_size_bytes / (1024 * 1024)
        message = f"File size OK ({file_size_mb:.2f} MB)"
        return True, message
    
    def validate_csv_structure(self, file_buffer) -> Dict:
        """
        Validate CSV file structure and required columns
        
        Args:
            file_buffer: File-like object or path to CSV file
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'column_info': {},
            'data_preview': None,
            'dataframe': None
        }
        
        try:
            # Read CSV
            df = pd.read_csv(file_buffer)
            validation_results['dataframe'] = df
            validation_results['data_preview'] = df.head()
            
            # Check if DataFrame is empty
            if df.empty:
                validation_results['errors'].append("CSV file is empty")
                validation_results['is_valid'] = False
                return validation_results
            
            # Normalize column names
            actual_columns = set(col.lower().strip() for col in df.columns)
            
            # Check for missing required columns
            missing_columns = set(self.required_columns) - actual_columns
            if missing_columns:
                validation_results['errors'].append(
                    f"Missing required columns: {', '.join(sorted(missing_columns))}"
                )
                validation_results['is_valid'] = False
            
            # Validate t24_customer_code column if present
            if 't24_customer_code' in actual_columns:
                # Find original column name with matching lowercase
                t24_col = None
                for col in df.columns:
                    if col.lower().strip() == 't24_customer_code':
                        t24_col = col
                        break
                
                if t24_col:
                    null_count = df[t24_col].isnull().sum()
                    unique_count = df[t24_col].nunique()
                    
                    if null_count > 0:
                        validation_results['warnings'].append(
                            f"t24_customer_code has {null_count} null values out of {len(df)} rows"
                        )
                    
                    validation_results['column_info']['t24_customer_code'] = {
                        'dtype': str(df[t24_col].dtype),
                        'null_count': int(null_count),
                        'unique_count': int(unique_count),
                        'sample_values': df[t24_col].dropna().head(5).tolist(),
                        'null_percentage': round((null_count / len(df)) * 100, 2)
                    }
            
            # General data quality checks
            validation_results['column_info']['general'] = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'duplicate_rows': int(df.duplicated().sum()),
                'column_names': list(df.columns)
            }
            
            logger.info(f"CSV validation completed: {len(df)} rows, {len(df.columns)} columns")
            
        except pd.errors.EmptyDataError:
            validation_results['errors'].append("CSV file is empty or corrupted")
            validation_results['is_valid'] = False
        except pd.errors.ParserError as e:
            validation_results['errors'].append(f"CSV parsing error: {str(e)}")
            validation_results['is_valid'] = False
        except Exception as e:
            validation_results['errors'].append(f"Unexpected error during validation: {str(e)}")
            validation_results['is_valid'] = False
            logger.error(f"CSV validation error: {str(e)}")
        
        return validation_results
    
    def validate_file(self, file_object) -> Dict:
        """
        Comprehensive file validation (size + structure)
        
        Args:
            file_object: Streamlit UploadedFile or file-like object
            
        Returns:
            Dictionary with complete validation results
        """
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'size_valid': False,
            'structure_valid': False,
            'file_size_mb': 0,
            'size_message': '',
            'validation_details': {}
        }
        
        try:
            # Get file size
            if hasattr(file_object, 'size'):
                file_size = file_object.size
            else:
                # For file-like objects
                file_object.seek(0, 2)  # Seek to end
                file_size = file_object.tell()
                file_object.seek(0)  # Reset to beginning
            
            results['file_size_mb'] = round(file_size / (1024 * 1024), 2)
            
            # Validate file size
            size_valid, size_message = self.validate_file_size(file_size)
            results['size_valid'] = size_valid
            results['size_message'] = size_message
            
            if not size_valid:
                results['errors'].append(size_message)
                results['is_valid'] = False
                return results
            
            # Reset file pointer and validate structure
            if hasattr(file_object, 'seek'):
                file_object.seek(0)
            
            structure_results = self.validate_csv_structure(file_object)
            results['structure_valid'] = structure_results['is_valid']
            results['validation_details'] = structure_results
            
            # Combine errors and warnings
            results['errors'].extend(structure_results['errors'])
            results['warnings'].extend(structure_results['warnings'])
            
            # Overall validation status
            results['is_valid'] = size_valid and structure_results['is_valid']
            
            logger.info(f"Overall validation result: is_valid={results['is_valid']}")
            
        except Exception as e:
            results['errors'].append(f"File validation failed: {str(e)}")
            results['is_valid'] = False
            logger.error(f"File validation error: {str(e)}")
        
        return results
