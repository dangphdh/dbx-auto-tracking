"""Databricks OAuth authentication handler"""

import streamlit as st
import requests
import base64
import secrets
from urllib.parse import urlencode, parse_qs
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabricksOAuthHandler:
    """Handle Databricks OAuth authentication flow"""
    
    def __init__(self, client_id: str, client_secret: str, server_hostname: str, redirect_uri: str):
        """
        Initialize OAuth handler
        
        Args:
            client_id: Databricks OAuth application client ID
            client_secret: Databricks OAuth application client secret
            server_hostname: Databricks workspace hostname (e.g., workspace.cloud.databricks.com)
            redirect_uri: OAuth callback redirect URI (e.g., http://localhost:8501/oauth_callback)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.server_hostname = server_hostname
        self.redirect_uri = redirect_uri
        
        # OAuth endpoints
        self.auth_url = f"https://{server_hostname}/oidc/v1/authorize"
        self.token_url = f"https://{server_hostname}/oidc/v1/token"
    
    def get_auth_url(self) -> str:
        """
        Generate authorization URL for user login
        
        Returns:
            Authorization URL to redirect user to
        """
        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)
        st.session_state.oauth_state = state
        st.session_state.oauth_state_timestamp = datetime.now()
        
        # Build authorization request
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'sql',
            'state': state
        }
        
        auth_url = f"{self.auth_url}?{urlencode(params)}"
        logger.info(f"Generated auth URL for client: {self.client_id}")
        
        return auth_url
    
    def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from OAuth callback
            state: State parameter from OAuth callback
            
        Returns:
            Token response containing access_token and other details
            
        Raises:
            ValueError: If state validation fails
            requests.RequestException: If token exchange fails
        """
        # Validate state parameter
        stored_state = st.session_state.get('oauth_state')
        if not stored_state or state != stored_state:
            logger.error("State parameter mismatch - possible CSRF attack")
            raise ValueError("Invalid state parameter - authentication failed")
        
        # Check if state has expired (15 minutes)
        state_timestamp = st.session_state.get('oauth_state_timestamp')
        if state_timestamp and (datetime.now() - state_timestamp) > timedelta(minutes=15):
            logger.error("OAuth state expired")
            raise ValueError("Authentication session expired - please try again")
        
        # Prepare token request
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        
        try:
            logger.info(f"Exchanging authorization code for access token")
            response = requests.post(self.token_url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            token_response = response.json()
            
            # Store token details in session
            st.session_state.access_token = token_response.get('access_token')
            st.session_state.token_type = token_response.get('token_type', 'Bearer')
            st.session_state.expires_in = token_response.get('expires_in')
            st.session_state.token_timestamp = datetime.now()
            
            logger.info("Successfully obtained access token")
            
            return token_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Token exchange failed: {str(e)}")
            raise ValueError(f"Failed to authenticate: {str(e)}")
    
    def is_token_valid(self) -> bool:
        """
        Check if stored access token is still valid
        
        Returns:
            True if token is valid and not expired, False otherwise
        """
        if 'access_token' not in st.session_state:
            return False
        
        token_timestamp = st.session_state.get('token_timestamp')
        expires_in = st.session_state.get('expires_in', 3600)  # Default 1 hour
        
        if not token_timestamp:
            return False
        
        # Check if token has expired (add 5 minute buffer)
        elapsed = (datetime.now() - token_timestamp).total_seconds()
        if elapsed > (expires_in - 300):
            logger.warning("Access token has expired")
            return False
        
        return True
    
    def get_access_token(self) -> Optional[str]:
        """
        Get valid access token from session
        
        Returns:
            Access token if valid, None otherwise
        """
        if self.is_token_valid():
            return st.session_state.access_token
        
        return None
    
    def logout(self):
        """Clear authentication session"""
        keys_to_clear = [
            'access_token', 'token_type', 'expires_in', 
            'token_timestamp', 'oauth_state', 'oauth_state_timestamp'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        logger.info("User logged out")


def initialize_oauth_session(client_id: str, client_secret: str, server_hostname: str, redirect_uri: str) -> DatabricksOAuthHandler:
    """
    Initialize OAuth handler and manage authentication flow in Streamlit
    
    Args:
        client_id: Databricks OAuth application client ID
        client_secret: Databricks OAuth application client secret
        server_hostname: Databricks workspace hostname
        redirect_uri: OAuth callback redirect URI
        
    Returns:
        DatabricksOAuthHandler instance
    """
    # Initialize OAuth handler
    oauth_handler = DatabricksOAuthHandler(
        client_id=client_id,
        client_secret=client_secret,
        server_hostname=server_hostname,
        redirect_uri=redirect_uri
    )
    
    # Check for OAuth callback parameters
    query_params = st.query_params
    
    if 'code' in query_params and 'state' in query_params:
        try:
            # Extract parameters (Streamlit returns lists)
            code = query_params['code'][0] if isinstance(query_params['code'], list) else query_params['code']
            state = query_params['state'][0] if isinstance(query_params['state'], list) else query_params['state']
            
            # Exchange code for token
            oauth_handler.exchange_code_for_token(code, state)
            
            # Clear query parameters and rerun
            st.query_params.clear()
            st.rerun()
            
        except ValueError as e:
            st.error(f"Authentication failed: {str(e)}")
            return oauth_handler
    
    return oauth_handler
