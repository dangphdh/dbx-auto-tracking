# Databricks CSV Auto-Tracking POC

A Streamlit-based web application that enables users to upload CSV files to Databricks Unity Catalog with OAuth authentication, automatic validation, and embedded dashboard visualization.

## Features

- 🔐 **OAuth Authentication**: Secure Databricks workspace authentication using OAuth 2.0
- 📁 **CSV Upload**: Upload CSV files directly to Databricks Unity Catalog Volumes
- ✅ **Smart Validation**: 
  - File type validation (CSV only)
  - Required column checking (`t24_customer_code`)
  - File size validation (10MB limit)
  - Data quality checks and profiling
- 📊 **Embedded Dashboards**: View Databricks dashboards directly in Streamlit
- 🔗 **Quick Links**: Direct links to Databricks exploration tools and SQL editor
- 📈 **Data Profiling**: View detailed information about your uploaded data

## Project Structure

```
dbx-auto-tracking/
├── app.py                          # Main Streamlit application
├── config.py                       # Configuration and settings
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── auth/
│   ├── __init__.py
│   └── databricks_oauth.py         # OAuth authentication handler
├── services/
│   ├── __init__.py
│   ├── csv_validator.py            # CSV validation logic
│   └── upload_service.py           # Databricks file upload service
├── components/
│   ├── __init__.py
│   └── embedded_dashboard.py       # Dashboard display components
└── README.md                       # This file
```

## Prerequisites

- Python 3.8+
- Databricks workspace with OAuth application configured
- SQL Warehouse or All-Purpose cluster for SQL execution
- Unity Catalog enabled on the workspace

## Installation

### 1. Clone the Repository

```bash
cd d:\Projects\dbx-auto-tracking
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your Databricks credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Databricks settings:

```env
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_CLIENT_ID=your-oauth-client-id
DATABRICKS_CLIENT_SECRET=your-oauth-client-secret
DATABRICKS_CATALOG=main
DATABRICKS_SCHEMA=default
DATABRICKS_VOLUME=csv_uploads
```

## Configuration

### Databricks OAuth Setup

1. **Create OAuth Application** in Databricks:
   - Go to Admin Settings → OAuth Applications
   - Create a new application
   - Set redirect URI to: `http://localhost:8501/oauth_callback`
   - Note the Client ID and Client Secret

2. **Create Unity Catalog Volume** (Optional):
   - Go to Catalog → Create Volume
   - Use catalog: `main`, schema: `default`, volume: `csv_uploads`
   - Or update `.env` with your volume path

3. **Create SQL Warehouse**:
   - Create a SQL warehouse if not already available
   - Note the HTTP path for `.env` configuration

## Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Usage Workflow

### 1. Authentication
- Click "Login with Databricks"
- Approve the OAuth request
- You'll be redirected back to the app

### 2. Upload CSV File
- Select a CSV file from your computer
- The app displays file information

### 3. Validation
- File is automatically validated:
  - File type (must be CSV)
  - File size (max 10MB)
  - Required columns (must include `t24_customer_code`)
  - Data quality checks

### 4. Upload to Databricks
- Review the validation results
- Configure target catalog, schema, and volume
- Click "Upload to Databricks"
- Monitor upload progress

### 5. Access Your Data
- Use quick links to explore data in Databricks
- View file location in Unity Catalog
- Execute SQL queries in SQL Editor
- Create dashboards for visualization

## CSV File Requirements

- **Format**: CSV (Comma-Separated Values)
- **Size**: Maximum 10MB
- **Required Columns**: `t24_customer_code`
- **Encoding**: UTF-8 recommended
- **Headers**: First row should contain column names

### Sample CSV Format

```csv
t24_customer_code,customer_name,account_number,balance
CUST001,John Doe,ACC123456,10000.00
CUST002,Jane Smith,ACC123457,25000.00
CUST003,Bob Johnson,ACC123458,15000.00
```

## API Reference

### CSVValidator

```python
from services.csv_validator import CSVValidator

validator = CSVValidator(
    required_columns=["t24_customer_code"],
    max_size_mb=10.0
)

results = validator.validate_file(file_object)
```

### DatabricksFilesAPIUploader

```python
from services.upload_service import DatabricksFilesAPIUploader

uploader = DatabricksFilesAPIUploader(
    server_hostname="workspace.cloud.databricks.com",
    access_token="your-access-token"
)

result = uploader.upload_file_to_volume(
    file_content=file_bytes,
    filename="data.csv",
    catalog="main",
    schema="default",
    volume="csv_uploads"
)
```

### DatabricksOAuthHandler

```python
from auth.databricks_oauth import DatabricksOAuthHandler

oauth = DatabricksOAuthHandler(
    client_id="client-id",
    client_secret="client-secret",
    server_hostname="workspace.cloud.databricks.com",
    redirect_uri="http://localhost:8501/oauth_callback"
)

auth_url = oauth.get_auth_url()
token = oauth.exchange_code_for_token(code, state)
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABRICKS_HOST` | Databricks workspace URL | `https://workspace.cloud.databricks.com` |
| `DATABRICKS_SERVER_HOSTNAME` | Workspace hostname | `workspace.cloud.databricks.com` |
| `DATABRICKS_HTTP_PATH` | SQL warehouse path | `/sql/1.0/warehouses/abc123` |
| `DATABRICKS_CLIENT_ID` | OAuth application client ID | `your-client-id` |
| `DATABRICKS_CLIENT_SECRET` | OAuth application client secret | `your-client-secret` |
| `DATABRICKS_CATALOG` | Target catalog name | `main` |
| `DATABRICKS_SCHEMA` | Target schema name | `default` |
| `DATABRICKS_VOLUME` | Target volume name | `csv_uploads` |
| `MAX_FILE_SIZE_MB` | Maximum file size in MB | `10` |
| `CSV_COLUMNS_REQUIRED` | Required CSV columns | `t24_customer_code` |

## Troubleshooting

### OAuth Authentication Issues

**Problem**: "Invalid state parameter" error
- **Solution**: OAuth state has expired. Try logging in again.

**Problem**: "Configuration error" message
- **Solution**: Verify all required environment variables in `.env` file are set correctly.

### File Upload Issues

**Problem**: "File size exceeds maximum" error
- **Solution**: Your CSV file is larger than 10MB. Compress or split the file.

**Problem**: "Missing required columns" error
- **Solution**: Ensure your CSV has a column named `t24_customer_code`.

**Problem**: "Connection failed" error
- **Solution**: Verify your Databricks workspace URL and SQL warehouse HTTP path.

### Streamlit Issues

**Problem**: Port 8501 already in use
- **Solution**: Run on a different port: `streamlit run app.py --server.port 8502`

**Problem**: SSL certificate verification errors
- **Solution**: For development only, you can disable certificate verification (not recommended for production):
  ```bash
  PYTHONHTTPSVERIFY=0 streamlit run app.py
  ```

## Advanced Features

### Automatic Job Triggering

After uploading files, you can set up Databricks Jobs to automatically process them:

1. Create a job in Databricks that reads from the volume
2. Configure a "File Arrival" trigger on the volume path
3. The job will run automatically when new files are uploaded

### Dashboard Integration

The app displays quick links to:
- **Catalog Explorer**: View files and tables in Unity Catalog
- **SQL Editor**: Write SQL queries to analyze data
- **Dashboards**: Create visualizations from your data

### Data Profiling

The app automatically provides:
- Row and column counts
- Unique value analysis for `t24_customer_code`
- Null value detection
- Duplicate row detection
- Sample data preview

## Performance Considerations

- **File Upload**: Large files (near 10MB) may take a few seconds to upload
- **Validation**: CSV parsing is performed locally on the Streamlit server
- **Network**: Upload speed depends on your connection to Databricks workspace

## Security Considerations

- OAuth tokens are stored securely in Streamlit session state
- Credentials are never logged or printed
- Use environment variables for all sensitive configuration
- Never commit `.env` file to version control
- Restrict access to the Streamlit app in production

## Future Enhancements

- [ ] Support for additional file formats (Parquet, JSON)
- [ ] Batch file upload support
- [ ] Automatic table schema inference
- [ ] Real-time data transformation preview
- [ ] Integration with Databricks AI/BI dashboards
- [ ] Multi-workspace support
- [ ] Scheduled file processing jobs

## Contributing

Contributions are welcome! Please:

1. Create a new branch for your feature
2. Add tests for new functionality
3. Update documentation as needed
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:

1. Check the Troubleshooting section
2. Review Databricks documentation: https://docs.databricks.com
3. Check Streamlit documentation: https://docs.streamlit.io

## Related Documentation

- [Databricks Unity Catalog Documentation](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)
- [Databricks OAuth Setup](https://docs.databricks.com/en/admin/auth/index.html)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Databricks Python SDK](https://github.com/databricks/databricks-sdk-py)
