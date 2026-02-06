"""Databricks CSV Auto-Tracking Streamlit Application"""

import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

# Import custom modules
from config import Config
from auth.databricks_oauth import initialize_oauth_session, DatabricksOAuthHandler
from services.csv_validator import CSVValidator
from services.upload_service import DatabricksUploader
from components.embedded_dashboard import (
    display_embedded_dashboard,
    display_uploaded_data_dashboard,
    display_data_profile_section,
    generate_dashboard_url
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit page configuration
st.set_page_config(
    page_title="Techcombank | Data Tracking",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Techcombank Red/Gray theme
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #FFFFFF;
    }
    
    /* Header styling */
    header[data-testid="stHeader"] {
        background-color: #E31D2E;
        color: white;
    }
    
    /* Red buttons */
    div.stButton > button:first-child {
        background-color: #E31D2E;
        color: white;
        border: none;
        border-radius: 4px;
    }
    div.stButton > button:first-child:hover {
        background-color: #B21724;
        color: white;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 1px solid #E9ECEF;
    }
    
    /* Custom containers */
    .main-container {
        padding: 2rem;
    }
    .upload-section {
        background-color: #F8F9FA;
        border: 1px solid #E9ECEF;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Metrics and indicators */
    [data-testid="stMetricValue"] {
        color: #E31D2E;
    }
    
    .success-box {
        background-color: #D4EDDA;
        border: 1px solid #C3E6CB;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .error-box {
        background-color: #F8D7DA;
        border: 1px solid #F5C6CB;
        color: #721C24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Title colors */
    h1, h2, h3 {
        color: #333333;
    }
    
    /* Style for the logo */
    .logo-container {
        display: flex;
        align-items: center;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)


def initialize_session_state():
    """Initialize all session state variables"""
    session_vars = {
        'authenticated': False,
        'access_token': None,
        'uploaded_file': None,
        'validation_results': None,
        'upload_complete': False,
        'upload_results': None,
        'current_step': 'authentication'
    }
    
    for key, default_value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def display_authentication_section():
    """Display OAuth authentication section"""
    st.header("🔐 Authentication")
    
    # Check if already authenticated
    if 'access_token' in st.session_state and st.session_state.access_token:
        st.success("✅ Authenticated with Databricks")
        
        if st.button("🔓 Logout"):
            st.session_state.access_token = None
            st.session_state.authenticated = False
            st.session_state.current_step = 'authentication'
            st.rerun()
        
        return True
    
    # OAuth authentication
    try:
        oauth_handler = initialize_oauth_session(
            client_id=Config.DATABRICKS_CLIENT_ID,
            client_secret=Config.DATABRICKS_CLIENT_SECRET,
            server_hostname=Config.DATABRICKS_SERVER_HOSTNAME,
            redirect_uri=Config.OAUTH_REDIRECT_URI
        )
        
        # Check if token is valid
        if oauth_handler.is_token_valid():
            st.session_state.authenticated = True
            st.session_state.access_token = oauth_handler.get_access_token()
            st.success("✅ Authenticated with Databricks")
            st.rerun()
        
        # Show login button
        if not st.session_state.authenticated:
            st.info("""
            👋 Please authenticate with your Databricks workspace to continue.
            Click the button below to log in.
            """)
            
            auth_url = oauth_handler.get_auth_url()
            
            # Display authentication button as markdown link
            st.markdown(
                f"[🔑 Login with Databricks]({auth_url})",
                unsafe_allow_html=True
            )
            
            st.info("""
            After clicking the login button:
            1. You'll be redirected to Databricks OAuth
            2. Approve the application
            3. You'll be redirected back to this app
            """)
            
            return False
    
    except ValueError as e:
        st.error(f"❌ Configuration error: {str(e)}")
        st.info("""
        Please ensure your `.env` file is configured with:
        - `DATABRICKS_CLIENT_ID`
        - `DATABRICKS_CLIENT_SECRET`
        - `DATABRICKS_SERVER_HOSTNAME`
        """)
        return False
    
    return True


def display_file_upload_section():
    """Display file upload and validation section"""
    st.header("📁 Upload CSV File")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload a CSV file containing T24 customer data (max 10MB)"
    )
    
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        
        # Display file information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size / (1024*1024):.2f} MB")
        with col3:
            st.metric("File Type", uploaded_file.type)
        
        return True
    
    return False


def display_validation_section():
    """Display CSV validation section"""
    st.header("✅ Validation")
    
    if st.session_state.uploaded_file is None:
        st.warning("⚠️ Please upload a file first")
        return False
    
    # Create validator
    validator = CSVValidator(
        required_columns=Config.CSV_COLUMNS_REQUIRED,
        max_size_mb=Config.MAX_FILE_SIZE_MB
    )
    
    # Validate file
    st.session_state.uploaded_file.seek(0)
    validation_results = validator.validate_file(st.session_state.uploaded_file)
    st.session_state.validation_results = validation_results
    
    # Display validation results
    if validation_results['is_valid']:
        st.success("✅ File validation passed!")
    else:
        st.error("❌ File validation failed!")
    
    # Display file size validation
    with st.expander("📏 File Size Check"):
        st.write(f"**File Size:** {validation_results['file_size_mb']} MB")
        st.write(f"**Max Allowed:** {Config.MAX_FILE_SIZE_MB} MB")
        
        if validation_results['size_valid']:
            st.success(validation_results['size_message'])
        else:
            st.error(validation_results['size_message'])
    
    # Display errors
    if validation_results['errors']:
        with st.expander("❌ Validation Errors"):
            for error in validation_results['errors']:
                st.error(error)
    
    # Display warnings
    if validation_results['warnings']:
        with st.expander("⚠️ Validation Warnings"):
            for warning in validation_results['warnings']:
                st.warning(warning)
    
    # Display column information
    if validation_results['validation_details'].get('column_info'):
        display_data_profile_section(
            validation_results['validation_details'].get('data_preview'),
            validation_results['validation_details'].get('column_info')
        )
    
    return validation_results['is_valid']


def display_upload_section():
    """Display file upload to Databricks section"""
    st.header("☁️ Upload to Databricks")
    
    if st.session_state.validation_results is None:
        st.warning("⚠️ Please validate the file first")
        return False
    
    if not st.session_state.validation_results['is_valid']:
        st.error("❌ Cannot upload - file validation failed")
        return False
    
    # Configuration for upload
    col1, col2, col3 = st.columns(3)
    
    with col1:
        catalog = st.text_input(
            "Catalog Name",
            value=Config.DATABRICKS_CATALOG,
            key="upload_catalog"
        )
    
    with col2:
        schema = st.text_input(
            "Schema Name",
            value=Config.DATABRICKS_SCHEMA,
            key="upload_schema"
        )
    
    with col3:
        volume = st.text_input(
            "Volume Name",
            value=Config.DATABRICKS_VOLUME,
            key="upload_volume"
        )
    
    volume_path = f"/Volumes/{catalog}/{schema}/{volume}"
    st.info(f"📍 Upload path: `{volume_path}`")
    
    # Upload button
    if st.button("🚀 Upload to Databricks", type="primary"):
        try:
            # Create uploader
            uploader = DatabricksUploader(
                server_hostname=Config.DATABRICKS_SERVER_HOSTNAME,
                http_path=Config.DATABRICKS_HTTP_PATH,
                access_token=st.session_state.access_token,
                client_id=Config.DATABRICKS_CLIENT_ID,
                client_secret=Config.DATABRICKS_CLIENT_SECRET
            )
            
            # Prepare file content
            st.session_state.uploaded_file.seek(0)
            file_content = st.session_state.uploaded_file.getvalue()
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def progress_callback(percentage, message):
                progress_bar.progress(percentage / 100)
                status_text.text(f"Progress: {percentage}% - {message}")
            
            # Upload file
            status_text.text("Starting upload...")
            
            upload_results = uploader.upload_file_to_volume(
                file_content=file_content,
                filename=st.session_state.uploaded_file.name,
                catalog=catalog,
                schema=schema,
                volume=volume,
                progress_callback=progress_callback
            )
            
            st.session_state.upload_results = upload_results
            st.session_state.upload_complete = upload_results['success']
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            if upload_results['success']:
                st.success("✅ File uploaded successfully!")
                st.json(upload_results)
                return True
            else:
                st.error(f"❌ Upload failed: {upload_results.get('error', 'Unknown error')}")
                return False
        
        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")
            logger.error(f"Upload error: {str(e)}")
            return False
    
    return False


def display_results_section():
    """Display upload results and dashboard information"""
    if not st.session_state.upload_complete or not st.session_state.upload_results:
        return
    
    st.header("📊 Upload Results")
    
    results = st.session_state.upload_results
    
    if results['success']:
        st.success("✅ File uploaded successfully to Databricks!")
        
        # Display upload details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("File Name", results.get('filename', 'N/A'))
        
        with col2:
            size_mb = results.get('size_bytes', 0) / (1024 * 1024)
            st.metric("File Size", f"{size_mb:.2f} MB")
        
        with col3:
            st.metric("Upload Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Display file path
        st.subheader("📍 File Location")
        st.code(results.get('path', 'N/A'))
        
        # Display Databricks links
        display_uploaded_data_dashboard(
            server_hostname=Config.DATABRICKS_SERVER_HOSTNAME,
            catalog=results.get('path', '').split('/')[2] if '/' in results.get('path', '') else Config.DATABRICKS_CATALOG,
            schema=results.get('path', '').split('/')[3] if '/' in results.get('path', '') else Config.DATABRICKS_SCHEMA,
            table_name=Path(results.get('filename', '')).stem,
            access_token=st.session_state.access_token
        )
        
        st.info("""
        🎉 **Your file has been uploaded successfully!**
        
        **Next steps:**
        1. Open the Databricks workspace using the links above
        2. Create a SQL query to analyze your data
        3. Configure Databricks Jobs to automatically process incoming files
        4. Create dashboards for data visualization
        
        The file is now available in your Unity Catalog Volume and ready for processing.
        """)


def main():
    """Main application"""
    # Initialize session state
    initialize_session_state()
    
    # Techcombank Header and Logo
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("https://www.techcombank.com.vn/themes/tcb/assets/images/logo.png", width=200)
    with col2:
        st.title("CSV Auto-Tracking & Validation")
        st.markdown("*Enterprise Data Ingestion Platform for Databricks Lakehouse*")
    
    st.divider()

    # Sidebar configuration
    with st.sidebar:
        st.image("https://www.techcombank.com.vn/themes/tcb/assets/images/logo.png", width=150)
        st.header("⚙️ POC Control Center")
        
        st.markdown("""
        <div style="background-color: #E31D2E; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;">
            <strong>POC MODE ACTIVE</strong><br/>
            Techcombank x Databricks
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("📍 Deployment Info")
        st.info(f"""
        **Host:** {Config.DATABRICKS_SERVER_HOSTNAME}
        **Catalog:** {Config.DATABRICKS_CATALOG}
        **Schema:** {Config.DATABRICKS_SCHEMA}
        **POC Warehouse:** Ready
        """)

        st.divider()
        
        st.subheader("📊 Monitoring")
        # Fixed POC Dashboard Link
        poc_url = generate_dashboard_url(Config.DATABRICKS_SERVER_HOSTNAME, Config.POC_DASHBOARD_ID)
        
        st.markdown(f"[🚀 Open POC Dashboard]({poc_url})")
        
        if st.checkbox("Show Embedded POC Dashboard", value=False):
            st.session_state.show_poc_dashboard = True
        else:
            st.session_state.show_poc_dashboard = False
        
        st.divider()
        
        st.subheader("📝 Instructions")
        with st.expander("How to use this app"):
            st.markdown("""
            1. **Authenticate** - Log in with your Databricks workspace
            2. **Upload** - Select and upload a CSV file
            3. **Validate** - The app validates file format and required columns
            4. **Confirm** - Review the file and click Upload
            5. **View** - Access your data in Databricks Unity Catalog
            
            **Requirements:**
            - File must be in CSV format
            - File size must be less than 10MB
            - Must contain `t24_customer_code` column
            """)
        
        st.divider()
        
        # Logout button (disabled - authentication skipped)
        # if st.session_state.authenticated:
        #     if st.button("🔓 Logout"):
        #         st.session_state.access_token = None
        #         st.session_state.authenticated = False
        #         st.session_state.current_step = 'authentication'
        #         st.rerun()
    
    # Main workflow logic with Tab selection
    tab1, tab2 = st.tabs(["🚀 Data Ingestion", "📊 POC Analytics"])
    
    with tab1:
        # Step 2: File Upload
        if not display_file_upload_section():
            st.info("👇 Please upload a CSV file to continue")
            st.stop()
        
        # Step 3: Validation
        st.divider()
        if not display_validation_section():
            st.stop()
        
        # Step 4: Upload
        st.divider()
        display_upload_section()
        
        # Step 5: Results
        st.divider()
        display_results_section()

    with tab2:
        st.header("📈 POC Performance Dashboard")
        st.info("Tracking ingestion latency, data quality trends, and system health.")
        
        # Use fixed POC ID from config
        poc_url = generate_dashboard_url(Config.DATABRICKS_SERVER_HOSTNAME, Config.POC_DASHBOARD_ID)
        
        display_embedded_dashboard(
            dashboard_url=poc_url,
            title="POC Real-time Monitoring",
            height=1000
        )


if __name__ == "__main__":
    main()
