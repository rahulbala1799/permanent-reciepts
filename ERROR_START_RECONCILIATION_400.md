# Error: 400 Bad Request on `/api/start-reconciliation`

## Error Details

**Error Code:** 400 Bad Request  
**Endpoint:** `POST /api/start-reconciliation/<job_id>/<subsidiary_id>`  
**Example:** `POST /api/start-reconciliation/6/5`  
**Error Message:** `"No Stripe transactions found for this job and subsidiary"`

## Where to Upload Stripe File

**Important:** The Stripe file upload is **NOT** on the main reconciliation page. You must navigate to the **subsidiary-specific reconciliation page** first.

### Step-by-Step Navigation:

1. **Start at Main Reconciliation Page:**
   - URL: `http://localhost:5001/reconciliation/6`
   - This page shows all subsidiaries as cards (AU, CA, US, EU, UK)
   - **The Stripe upload button is NOT here**

2. **Click on a Subsidiary Card:**
   - Click on the subsidiary you want to reconcile (e.g., "UK" card)
   - This navigates to the subsidiary-specific page

3. **Subsidiary-Specific Reconciliation Page:**
   - URL: `http://localhost:5001/reconciliation/6/5` (for job 6, subsidiary 5)
   - **This is where the Stripe upload button is located**

4. **Find the "Upload Stripe File" Button:**
   - **Location:** Top right button group on the page
   - **Appearance:** Yellow/Warning colored button
   - **Icon:** File CSV icon (`<i class="fas fa-file-csv"></i>`)
   - **Text:** "Upload Stripe File"
   - **Position:** Second button in the button group (after "Back to Job")

5. **Upload Process:**
   - Click "Upload Stripe File" button
   - Modal dialog opens: "Upload Stripe CSV File for [Subsidiary Name]"
   - Select your CSV file
   - Click "Upload Stripe File" in the modal
   - Wait for success message

### Visual Guide:

```
Subsidiary Reconciliation Page Layout:
┌─────────────────────────────────────────────────────────┐
│ [Back] [Upload Stripe File] [View Stripe] [Upload Cashbook] │
│                    ↑                                        │
│              THIS BUTTON                                    │
└─────────────────────────────────────────────────────────┘
```

**File Location:** `templates/subsidiary_reconciliation.html` line 36-37

## Why This Error Occurs

The `/api/start-reconciliation` endpoint requires **Stripe transactions** to exist in the database before reconciliation can start. The error occurs when:

1. **No Stripe CSV file has been uploaded** for the specified job and subsidiary
2. **Stripe transactions were deleted** from the database
3. **Wrong job_id or subsidiary_id** is being used
4. **Stripe upload failed** but the error wasn't noticed

## Root Cause Analysis

### Code Location
The error is generated in `app.py` at lines 4241-4242:

```python
@app.route('/api/start-reconciliation/<int:job_id>/<int:subsidiary_id>', methods=['POST'])
def start_reconciliation(job_id, subsidiary_id):
    try:
        # Get all Stripe transactions for this job and subsidiary
        stripe_transactions = StripeTransaction.query.filter_by(
            job_id=job_id,
            subsidiary_id=subsidiary_id
        ).all()
        
        if not stripe_transactions:
            return jsonify({'error': 'No Stripe transactions found for this job and subsidiary'}), 400
```

### Validation Logic
The endpoint performs this check:
1. Queries the database for `StripeTransaction` records matching `job_id` and `subsidiary_id`
2. If the query returns an empty list, it returns a 400 error
3. This is a **required validation** - reconciliation cannot proceed without Stripe data

## How to Fix This Error

### Solution 1: Upload Stripe CSV File (Most Common Fix)

**Step 1: Navigate to the Subsidiary Reconciliation Page**
- The Stripe upload is located on the **subsidiary-specific reconciliation page**
- Go to: `/reconciliation/<job_id>/<subsidiary_id>`
- Example: `http://localhost:5001/reconciliation/6/5`
- **Note:** This is different from the main reconciliation page (`/reconciliation/<job_id>`)

**Navigation Flow:**
1. Start at main reconciliation page: `/reconciliation/6` (shows all subsidiaries)
2. Click on a subsidiary card (e.g., "UK" for subsidiary_id=5)
3. This navigates to: `/reconciliation/6/5` (subsidiary-specific page)
4. **This is where you upload the Stripe file**

**Step 2: Upload Stripe CSV File**
1. On the subsidiary reconciliation page, look for the **"Upload Stripe File"** button
   - It's a yellow/warning colored button with icon: `<i class="fas fa-file-csv"></i> Upload Stripe File`
   - Located in the top button group on the page
2. Click the **"Upload Stripe File"** button
3. A modal dialog will open titled: "Upload Stripe CSV File for [Subsidiary Name]"
4. Click "Choose File" and select your Stripe CSV file
5. Click **"Upload Stripe File"** button in the modal
6. Wait for upload to complete
7. You should see a success message: "Successfully uploaded X Stripe transactions!"
8. The "View Stripe Data" button will become enabled and show the transaction count

**Step 3: Verify Stripe Transactions Exist**
- Check the Stripe transactions count on the page
- Or use the API: `GET /api/stripe-transactions/6/5`
- Should return a list of transactions (not empty array)

**Step 4: Retry Reconciliation**
- Click "Start Reconciliation" button again
- The error should be resolved

### Solution 2: Check Database Directly

**Verify Stripe transactions exist in database:**
```bash
# Connect to PostgreSQL
psql -U receipts_user -d receipts_dev

# Check for Stripe transactions
SELECT COUNT(*) FROM stripe_transactions 
WHERE job_id = 6 AND subsidiary_id = 5;

# If count is 0, transactions don't exist
# If count > 0, transactions exist but may have other issues
```

**If transactions don't exist:**
- Upload Stripe CSV file using the web interface
- Or use the API endpoint: `POST /api/stripe-upload/6/5`

### Solution 3: Verify Job and Subsidiary IDs

**Check that you're using the correct IDs:**
1. Verify job exists: `GET /api/jobs/6`
2. Verify subsidiary exists: `GET /api/subsidiaries`
3. Check that subsidiary_id=5 is valid (should be one of: 1=AU, 2=CA, 3=US, 4=EU, 5=UK)

**Common mistakes:**
- Using wrong subsidiary_id
- Using job_id that doesn't exist
- Mixing up job_id and subsidiary_id

### Solution 4: Check Upload History

**Review what files were uploaded:**
1. Check the reconciliation page for uploaded files list
2. Look for any error messages from previous uploads
3. Verify the Stripe CSV file format is correct

**Required Stripe CSV format:**
- Must be a valid CSV file
- Should contain columns like: amount, date, fees, etc.
- See Stripe export format requirements

## Prevention: Correct Workflow

To avoid this error, follow the **correct reconciliation workflow**:

### Step-by-Step Process

1. **Create a Job**
   ```
   POST /api/jobs
   {
     "job_name": "Reconciliation Job 6",
     "job_description": "Description"
   }
   ```

2. **Navigate to Main Reconciliation Page**
   - Go to: `/reconciliation/<job_id>`
   - Example: `/reconciliation/6`
   - This page shows all subsidiaries as cards

3. **Select Subsidiary**
   - Click on a subsidiary card (e.g., "UK" for subsidiary_id=5)
   - This navigates to: `/reconciliation/<job_id>/<subsidiary_id>`
   - Example: `/reconciliation/6/5` (Job 6, Subsidiary 5 = UK)
   - **This is the subsidiary-specific reconciliation page**

4. **Upload Stripe CSV File** ⚠️ REQUIRED
   - On the subsidiary reconciliation page, click the **"Upload Stripe File"** button (yellow/warning button)
   - In the modal that opens, select your Stripe CSV file
   - Click "Upload Stripe File" in the modal
   - Wait for success message: "Successfully uploaded X Stripe transactions!"
   - The "View Stripe Data" button should now be enabled
   
   **API Endpoint Used:**
   ```
   POST /api/stripe-upload/6/5
   Content-Type: multipart/form-data
   file: [Stripe CSV file]
   ```

4. **Upload Cashbook Excel File** (Optional but recommended)
   ```
   POST /api/cashbook-upload/6/5
   Content-Type: multipart/form-data
   file: [Cashbook Excel file]
   ```

5. **Start Reconciliation** ✅
   ```
   POST /api/start-reconciliation/6/5
   ```
   - This should now work because Stripe transactions exist

## Debugging Steps

### 1. Check API Response
```bash
# Test the endpoint directly
curl -X POST http://localhost:5001/api/start-reconciliation/6/5

# Expected error response:
# {"error": "No Stripe transactions found for this job and subsidiary"}
```

### 2. Verify Stripe Transactions Endpoint
```bash
# Check if transactions exist
curl http://localhost:5001/api/stripe-transactions/6/5

# If empty array [], then no transactions exist
# If array with data, transactions exist
```

### 3. Check Browser Console
- Open browser developer tools (F12)
- Go to Network tab
- Look for the `/api/start-reconciliation/6/5` request
- Check the response body for error details

### 4. Check Server Logs
- Look at the Flask application console output
- Check for any database connection errors
- Look for any exceptions during the query

## Common Scenarios

### Scenario 1: First Time Using This Job/Subsidiary
**Problem:** New job created, no files uploaded yet  
**Solution:** Upload Stripe CSV file first

### Scenario 2: Transactions Were Deleted
**Problem:** Someone deleted Stripe transactions from database  
**Solution:** Re-upload the Stripe CSV file

### Scenario 3: Wrong Subsidiary Selected
**Problem:** Uploaded to subsidiary 3, but trying to reconcile subsidiary 5  
**Solution:** Either upload to correct subsidiary or use correct subsidiary_id

### Scenario 4: Upload Failed Silently
**Problem:** Upload appeared to succeed but transactions weren't saved  
**Solution:** 
- Check server logs for upload errors
- Verify file format is correct
- Try uploading again
- Check database directly

## API Endpoints Reference

### Upload Stripe CSV
```
POST /api/stripe-upload/<job_id>/<subsidiary_id>
Content-Type: multipart/form-data
Body: file (CSV file)
```

### Get Stripe Transactions
```
GET /api/stripe-transactions/<job_id>/<subsidiary_id>
Response: Array of StripeTransaction objects
```

### Start Reconciliation
```
POST /api/start-reconciliation/<job_id>/<subsidiary_id>
Response: {
  "message": "Reconciliation started successfully",
  "fees_calculation": {...},
  "total_transactions": 123
}
```

## Error Response Format

**When error occurs:**
```json
{
  "error": "No Stripe transactions found for this job and subsidiary"
}
```

**HTTP Status:** 400 Bad Request

## Success Response Format

**When reconciliation starts successfully:**
```json
{
  "message": "Reconciliation started successfully",
  "fees_calculation": {
    "column_i_fees": {
      "total": 1234.56,
      "count": 100,
      "description": "..."
    },
    ...
  },
  "total_transactions": 100
}
```

**HTTP Status:** 200 OK

## Quick Fix Checklist

- [ ] Navigate to the **subsidiary-specific reconciliation page**: `/reconciliation/6/5`
  - **Not** the main reconciliation page (`/reconciliation/6`)
  - Must click on a subsidiary card first to get to the subsidiary page
- [ ] Look for the **"Upload Stripe File"** button (yellow/warning button in top button group)
- [ ] Click "Upload Stripe File" button to open the upload modal
- [ ] Select your Stripe CSV file in the modal
- [ ] Click "Upload Stripe File" in the modal
- [ ] Verify upload was successful (check for success message: "Successfully uploaded X transactions!")
- [ ] Check that "View Stripe Data" button is now enabled (shows transaction count)
- [ ] Confirm Stripe transactions exist: `GET /api/stripe-transactions/6/5`
- [ ] If no transactions, upload Stripe CSV file using the button on subsidiary page
- [ ] Retry reconciliation after upload

## Related Files

- **Backend:** `app.py` lines 4232-4254 (start-reconciliation endpoint)
- **Backend Upload:** `app.py` lines 2190-2314 (stripe-upload endpoint)
- **Frontend Main Page:** `templates/reconciliation.html` (shows all subsidiaries)
- **Frontend Subsidiary Page:** `templates/subsidiary_reconciliation.html` (where Stripe upload button is located)
  - Line 36-37: "Upload Stripe File" button
  - Line 250-277: Stripe upload modal
  - Line 385-431: uploadStripeFile() JavaScript function
- **Model:** `models.py` - `StripeTransaction` class

## Summary

**The 400 error occurs because:**
- No Stripe transactions exist in the database for the specified job and subsidiary
- Reconciliation requires Stripe data to calculate fees and begin matching

**Where to Upload Stripe File:**
- **Location:** Subsidiary-specific reconciliation page (`/reconciliation/<job_id>/<subsidiary_id>`)
- **Not on:** Main reconciliation page (`/reconciliation/<job_id>`)
- **Button:** "Upload Stripe File" (yellow/warning button in top button group)
- **How:** Click button → Modal opens → Select CSV file → Click "Upload Stripe File" in modal

**To fix:**
1. Navigate to `/reconciliation/6/5` (subsidiary-specific page)
2. Click "Upload Stripe File" button
3. Select and upload your Stripe CSV file in the modal
4. Verify success message appears
5. Retry the reconciliation

**Prevention:**
- Always navigate to the **subsidiary-specific page** first (click subsidiary card)
- Upload Stripe CSV file using the "Upload Stripe File" button on that page
- Verify transactions exist (check "View Stripe Data" button is enabled)
- Follow the correct workflow: Create Job → Select Subsidiary → Upload Stripe → Upload Cashbook → Start Reconciliation

---

**Last Updated:** 1 January 2026  
**Error Code:** 400  
**Severity:** User Error (Fixable by following correct workflow)
