"""Embedded Databricks Dashboard component"""

import streamlit as st
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def display_embedded_dashboard(
    dashboard_url: str,
    title: str = "Databricks Dashboard",
    height: int = 800
) -> None:
    """
    Display embedded Databricks dashboard using iframe
    
    Args:
        dashboard_url: Full URL to Databricks dashboard
        title: Title to display above dashboard
        height: Height of iframe in pixels
    """
    st.subheader(title)
    
    # Display dashboard using iframe
    st.components.v1.html(
        f"""
        <iframe
            src="{dashboard_url}"
            width="100%"
            height="{height}"
            frameborder="0"
            allow="fullscreen"
        ></iframe>
        """,
        height=height
    )


def display_dashboard_link(
    dashboard_url: str,
    dashboard_name: str = "Dashboard"
) -> None:
    """
    Display a clickable link to Databricks dashboard
    
    Args:
        dashboard_url: Full URL to Databricks dashboard
        dashboard_name: Name of the dashboard
    """
    st.markdown(
        f"""
        ### 📊 View Dashboard
        
        Click the link below to view the dashboard in a new window:
        
        [🔗 Open {dashboard_name}]({dashboard_url})
        
        Or scan this QR code:
        """
    )


def generate_dashboard_url(
    server_hostname: str,
    dashboard_id: str,
    embed: bool = True
) -> str:
    """
    Generate Databricks dashboard URL
    
    Args:
        server_hostname: Databricks workspace hostname
        dashboard_id: ID of the dashboard (from Unity Catalog metadata)
        embed: Whether to generate an embed URL (for iframe)
        
    Returns:
        Full dashboard URL
    """
    base_url = f"https://{server_hostname}"
    
    if embed:
        # Embedded dashboard URL format
        dashboard_url = f"{base_url}/embed/dashboards/{dashboard_id}"
    else:
        # Standard dashboard URL format
        dashboard_url = f"{base_url}/explore/dashboards/{dashboard_id}"
    
    logger.info(f"Generated dashboard URL: {dashboard_url}")
    return dashboard_url


def display_uploaded_data_dashboard(
    server_hostname: str,
    catalog: str,
    schema: str,
    table_name: str,
    access_token: str
) -> None:
    """
    Display information about the uploaded data table
    
    Args:
        server_hostname: Databricks workspace hostname
        catalog: Catalog name
        schema: Schema name
        table_name: Table name
        access_token: OAuth access token for Databricks
    """
    st.subheader("📊 Data Upload Information")
    
    # Display table information
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Catalog", catalog)
    
    with col2:
        st.metric("Schema", schema)
    
    with col3:
        st.metric("Table", table_name)
    
    with col4:
        st.metric("Status", "✅ Ready")
    
    # Full table path
    full_table_path = f"{catalog}.{schema}.{table_name}"
    st.code(full_table_path, language="sql")
    
    # Links to explore data
    st.subheader("🔗 Quick Links")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        catalog_url = f"https://{server_hostname}/explore/data/{catalog}/{schema}/{table_name}"
        st.markdown(f"[📂 View in Catalog Explorer]({catalog_url})")
    
    with col2:
        sql_editor_url = f"https://{server_hostname}/sql/editor"
        st.markdown(f"[📝 Open SQL Editor]({sql_editor_url})")
    
    with col3:
        dashboard_url = f"https://{server_hostname}/explore/dashboards"
        st.markdown(f"[📊 View Dashboards]({dashboard_url})")
    
    # Sample SQL query
    st.subheader("📋 Sample Query")
    
    sample_query = f"SELECT * FROM {full_table_path} LIMIT 10;"
    st.code(sample_query, language="sql")
    
    # Instructions
    with st.expander("ℹ️ How to create a dashboard"):
        st.markdown("""
        1. Navigate to your Databricks workspace
        2. Open the SQL Editor from the links above
        3. Write your SQL query against the uploaded table
        4. Click "Create Dashboard" or save as a query
        5. Configure visualization widgets
        6. Save and share your dashboard
        
        **For automatic dashboard creation:**
        - Create a Databricks job that runs on file upload
        - Use Databricks Workflows to trigger the job
        - Configure the job to create dashboard objects via SQL
        """)


def display_data_profile_section(
    dataframe_preview,
    column_info: dict
) -> None:
    """
    Display data profile and validation information
    
    Args:
        dataframe_preview: First few rows of uploaded data
        column_info: Column validation information
    """
    st.subheader("📈 Data Profile")
    
    if column_info and 'general' in column_info:
        general_info = column_info['general']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Rows", general_info.get('total_rows', 0))
        
        with col2:
            st.metric("Total Columns", general_info.get('total_columns', 0))
        
        with col3:
            st.metric("Duplicate Rows", general_info.get('duplicate_rows', 0))
        
        with col4:
            t24_info = column_info.get('t24_customer_code', {})
            st.metric("Unique Customers", t24_info.get('unique_count', 0))
    
    # Display column details
    st.subheader("📋 Column Details")
    
    if 't24_customer_code' in column_info:
        t24_data = column_info['t24_customer_code']
        
        with st.expander("🔍 t24_customer_code"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Data Type:** {t24_data.get('dtype', 'N/A')}")
                st.write(f"**Unique Values:** {t24_data.get('unique_count', 0)}")
            
            with col2:
                st.write(f"**Null Values:** {t24_data.get('null_count', 0)}")
                st.write(f"**Null Percentage:** {t24_data.get('null_percentage', 0)}%")
            
            if t24_data.get('sample_values'):
                st.write("**Sample Values:**")
                st.write(t24_data['sample_values'])
    
    # Display data preview
    st.subheader("👁️ Data Preview")
    st.dataframe(dataframe_preview, use_container_width=True)
