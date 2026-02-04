# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies (1 min)
```bash
cd d:\Projects\dbx-auto-tracking
pip install -r requirements.txt
```

### Step 2: Configure Environment (2 min)

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your Databricks details:
```env
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_CLIENT_ID=your-client-id
DATABRICKS_CLIENT_SECRET=your-client-secret
```

**How to find these values:**

1. **Server Hostname**: In Databricks, click your workspace name in top-left, copy the URL
   - Format: `adb-1234567890.cloud.databricks.com`

2. **HTTP Path**: Go to SQL Workspaces → SQL Warehouses → Select warehouse → Click "Connection details"
   - Format: `/sql/1.0/warehouses/abc123def456`

3. **Client ID & Secret**: 
   - Go to Admin Settings → OAuth Applications → Create New Application
   - Set Redirect URI to: `http://localhost:8501/oauth_callback`
   - Copy Client ID and Secret to `.env`

### Step 3: Run the App (2 min)

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

## Usage

1. **Login**: Click "Login with Databricks" button
2. **Upload**: Select your CSV file (must have `t24_customer_code` column, max 10MB)
3. **Validate**: App checks file format and structure automatically
4. **Upload**: Click "Upload to Databricks" button
5. **View**: Use the quick links to explore your data in Databricks

## Example CSV Format

Create a test file `test_data.csv`:

```csv
t24_customer_code,customer_name,account_number,balance,branch_code
CUST001,John Doe,ACC001,50000.00,BNK001
CUST002,Jane Smith,ACC002,75000.00,BNK002
CUST003,Bob Johnson,ACC003,60000.00,BNK001
CUST004,Alice Williams,ACC004,85000.00,BNK003
CUST005,Charlie Brown,ACC005,45000.00,BNK002
```

## Common Issues

**"Missing configuration" error**
- Verify all fields in `.env` are filled in
- Check there are no spaces after `=` in `.env`

**"Connection failed" error**
- Verify Server Hostname and HTTP Path are correct
- Test connection in Databricks SQL Editor first

**"OAuth error" error**
- Ensure redirect URI in OAuth app is: `http://localhost:8501/oauth_callback`
- Clear browser cookies and try again

## Next Steps

After successful upload:

1. **Explore Data**
   - Click "View in Catalog Explorer" link
   - Browse the file in your Unity Catalog Volume

2. **Create SQL Queries**
   - Click "Open SQL Editor" link
   - Run queries against the uploaded data
   - Example: `SELECT * FROM main.default.test_data LIMIT 10`

3. **Create Dashboards**
   - In Databricks, create a new Dashboard
   - Add visualizations based on your data
   - Share with team members

4. **Automate Processing**
   - Create a Databricks Job
   - Set up File Arrival trigger on your volume
   - Job runs automatically when new files are uploaded

## Troubleshooting Commands

Check Python version:
```bash
python --version
```

Check installed packages:
```bash
pip list
```

Check Streamlit status:
```bash
streamlit --version
```

Run with debug logging:
```bash
streamlit run app.py --logger.level=debug
```

## Architecture Overview

```
User Browser
     ↓
Streamlit App (Port 8501)
     ├── OAuth Handler (Login)
     ├── CSV Validator (File checks)
     ├── Upload Service (Databricks API)
     └── Dashboard Display (Links)
     ↓
Databricks Workspace
     ├── OAuth Server (Authentication)
     ├── SQL Warehouse (Data processing)
     ├── Unity Catalog (Data storage)
     └── Dashboards (Visualization)
```

## Files Overview

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application |
| `config.py` | Configuration management |
| `auth/databricks_oauth.py` | OAuth authentication |
| `services/csv_validator.py` | CSV validation logic |
| `services/upload_service.py` | File upload to Databricks |
| `components/embedded_dashboard.py` | Dashboard UI components |

## Performance Tips

- Upload during off-peak hours for faster processing
- Keep CSV files under 5MB for optimal performance
- Use a dedicated SQL Warehouse with at least 1 cluster

## Security Notes

- Never share your `.env` file
- Regenerate OAuth secrets if exposed
- Use strong passwords for Databricks
- Restrict Streamlit app access in production

## Support Resources

- Databricks Docs: https://docs.databricks.com
- Streamlit Docs: https://docs.streamlit.io
- OAuth Setup: https://docs.databricks.com/en/admin/auth/oauth.html

---

**Ready to get started?** Run `streamlit run app.py` and begin uploading your CSV files! 🚀
