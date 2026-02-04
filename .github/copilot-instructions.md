# Copilot Instructions for dbx-auto-tracking

## Project Overview

**Databricks CSV Auto-Tracking** is a Streamlit web application that enables secure CSV uploads to Databricks Unity Catalog with OAuth authentication, automatic validation, and dashboard integration.

- **Language**: Python 3.8+
- **Framework**: Streamlit 1.40.2
- **External Integration**: Databricks SDK (SQL Connector, databricks-sdk)
- **Primary Use Case**: Enterprise CSV data ingestion with compliance validation

## Architecture & Data Flow

### Component Structure (Modular Design)

```
app.py (Streamlit UI orchestrator)
├── auth/databricks_oauth.py (OAuth 2.0 handler)
├── services/csv_validator.py (CSV validation logic)
├── services/upload_service.py (Files API uploader)
└── components/embedded_dashboard.py (Dashboard UI)
config.py (Environment-driven configuration)
```

### Request Flow (Linear Multi-Step Workflow)

1. **Authentication**: OAuth flow → token stored in `st.session_state`
2. **File Upload**: Streamlit file uploader → `st.session_state.uploaded_file`
3. **Validation**: CSVValidator checks size, columns, data quality → validation_results dict
4. **Upload**: DatabricksFilesAPIUploader → `/Volumes/{catalog}/{schema}/{volume}/{filename}`
5. **Results**: Display success/failure with Databricks links

**Key Pattern**: Each step blocks progress until previous step succeeds (`st.stop()` gates).

## Critical Implementation Details

### OAuth Authentication Flow

- Uses Databricks OIDC endpoints: `https://{hostname}/oidc/v1/authorize` and `https://{hostname}/oidc/v1/token`
- **CSRF Protection**: State parameter validated during token exchange (stored in `st.session_state.oauth_state`)
- **Token Validation**: Check expiration before use (`is_token_valid()` method)
- Auth URL includes `scope: 'sql'` for SQL warehouse access
- Redirect URI must be pre-registered in Databricks OAuth app settings

### CSV Validation Logic

Required validation sequence in `CSVValidator.validate_file()`:
1. File size check (max 10MB, configurable)
2. CSV structure parsing (Pandas read_csv)
3. Column name normalization (lowercase, strip whitespace)
4. Required columns validation (config: `t24_customer_code`)
5. Data quality profiling (null counts, duplicates, data types)

**Return Type**: Dict with keys: `is_valid`, `errors`, `warnings`, `file_size_mb`, `size_valid`, `size_message`, `validation_details` (includes `dataframe`, `data_preview`, `column_info`)

### File Upload to Unity Catalog

- **Uploader Class**: `DatabricksFilesAPIUploader` (alternate: `DatabricksUploader` for SQL connection)
- **API Used**: Databricks Files API (preferred over SQL PUT statements)
- **Auth Method**: OAuth access token as PAT
- **Volume Path Construction**: `/Volumes/{catalog}/{schema}/{volume}/{filename}`
- **Progress Callback**: Optional callback receives (percentage, message) for real-time UI updates
- **Connection Pooling**: Connection reused across multiple uploads (check `self.connection` state)

### Session State Variables

Critical Streamlit state tracked across reruns:
- `authenticated` (bool)
- `access_token` (str) - OAuth bearer token
- `uploaded_file` - UploadedFile object (seek(0) before each read)
- `validation_results` - Full validation dict
- `upload_complete` (bool)
- `upload_results` - Server response with path, size_bytes, success
- `current_step` - Workflow step enum

## Configuration Management

**Source**: Environment variables via `.env` file (loaded by [config.py](config.py))

**Critical Config Values**:
- `DATABRICKS_HOST` - Full workspace URL
- `DATABRICKS_SERVER_HOSTNAME` - Hostname only (for OAuth)
- `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET` - OAuth credentials
- `DATABRICKS_HTTP_PATH` - SQL warehouse path for SQL Connector
- `DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA`, `DATABRICKS_VOLUME` - Unity Catalog path
- `CSV_COLUMNS_REQUIRED` - Comma-separated list (default: `t24_customer_code`)
- `MAX_FILE_SIZE_MB` - Upload size limit (default: 10)
- `OAUTH_REDIRECT_URI` - Must match Databricks app settings (default: `http://localhost:8501/oauth_callback`)

**Validation**: `Config.validate()` runs on import; raises ValueError if required fields missing.

## Developer Workflows

### Running the Application

```bash
# Activate venv
venv\Scripts\activate

# Run Streamlit app
streamlit run app.py

# Default: http://localhost:8501
```

### Testing OAuth Flow Locally

1. Verify `.env` has valid OAuth credentials
2. Redirect URI must be `http://localhost:8501/oauth_callback` in Databricks OAuth app
3. Check browser console for auth URL redirect issues
4. OAuth state validation occurs in `DatabricksOAuthHandler.exchange_code_for_token()`

### Adding New Validation Rules

1. Add logic to `CSVValidator.validate_csv_structure()` or new method
2. Append to `validation_results['errors']` or `validation_results['warnings']`
3. Call validator before upload in `display_validation_section()`

### Extending with Dashboard Integration

- Use `embedded_dashboard.py` functions: `display_embedded_dashboard()`, `display_dashboard_link()`, `generate_dashboard_url()`
- Pass `server_hostname` (from Config) and `dashboard_id` to generate iframe URLs
- Iframe URLs require workspace subdomain in `src` attribute

## Project-Specific Conventions

1. **Logging**: All modules use `logging.basicConfig(level=logging.INFO)` with module-level logger
2. **Error Handling**: Services raise exceptions; app.py catches and displays as `st.error()`
3. **Type Hints**: Used throughout (Dict, List, Optional, Callable, Tuple)
4. **Streamlit Patterns**:
   - Callbacks for progress: `progress_callback(percentage, message)`
   - File reopening: Always `uploaded_file.seek(0)` before reading
   - Session barriers: Use `st.stop()` to prevent code execution after warnings
5. **Return Types**: Service methods return dicts with `success` boolean + metadata (files, errors, paths)

## Key Files Reference

- [app.py](app.py) - Main Streamlit app; workflow orchestration (472 lines)
- [auth/databricks_oauth.py](auth/databricks_oauth.py) - OAuth handler; token exchange logic (220 lines)
- [services/csv_validator.py](services/csv_validator.py) - CSV validation; data profiling (204 lines)
- [services/upload_service.py](services/upload_service.py) - Files API uploader; connection mgmt (308 lines)
- [components/embedded_dashboard.py](components/embedded_dashboard.py) - Dashboard components; iframe rendering (227 lines)
- [config.py](config.py) - Environment config loader; validation (57 lines)

## Common Integration Points

- **Databricks SDK**: `databricks.sql.connect()` for warehouse connections; Files API for uploads
- **Streamlit Query Params**: OAuth redirect uses `st.query_params['code']` and `st.query_params['state']`
- **Pandas**: Used in validator for CSV parsing and profiling
- **Requests Library**: Used in OAuth handler for token exchange HTTP calls

## When Modifying This Codebase

- **Adding Features**: Check if Streamlit reruns affect session state assumptions
- **OAuth Changes**: Test with real Databricks workspace; state validation is critical
- **New Upload Methods**: Extend `DatabricksFilesAPIUploader` class; keep progress_callback signature
- **Validation Rules**: Always return consistent dict structure from validate methods
