# Permanent Receipts - Financial Reconciliation & Journal Processing System

A comprehensive Flask-based web application for automating financial reconciliation, journal processing, and transaction matching across multiple subsidiaries. This system handles Stripe transactions, cashbook entries, manual payments, BACS reviews, and generates accounting journals for various financial processes.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Database Models](#database-models)
- [Main Features & Workflows](#main-features--workflows)
- [API Endpoints](#api-endpoints)
- [How It Works](#how-it-works)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

---

## Overview

This application is designed to automate complex financial reconciliation processes for a multi-subsidiary organization. It processes various types of financial data including:

- **Stripe Transactions**: Payment processing data from Stripe
- **Cashbook Entries**: Bank statement and cashbook data
- **Manual Payments**: Manual payment processing and automation
- **BACS Reviews**: BACS payment review and processing
- **Journal Generation**: Automated accounting journal creation

The system supports 5 subsidiaries:
1. Phorest Australia (AU)
2. Canada (CA)
3. USA (US)
4. EU (EU)
5. UK (UK)

---

## Features

### Core Features

1. **Multi-Subsidiary Reconciliation**
   - Individual subsidiary processing
   - Cross-subsidiary transaction handling
   - Region-specific workflows

2. **Transaction Matching**
   - Perfect match detection (exact amount and date)
   - Date-amount matching with tolerance
   - Near-match detection with fuzzy logic
   - Multiple matching processes (Process 1, 2, 3)

3. **File Processing**
   - Excel/CSV file upload and processing
   - Looker cashbook data integration
   - File preparation and conversion
   - Automated data validation

4. **Journal Generation**
   - Main journal generation
   - POA (Proof of Account) journals
   - Refunds journals
   - Cross-subsidiary split journals
   - Summit installments processing
   - EU-specific journal processing

5. **Automation Modules**
   - Stripe automation processing
   - Manual payment automation
   - BACS review automation
   - Summit installments automation

6. **Data Management**
   - Transaction data viewing and editing
   - Error fixing and validation
   - Data export and download
   - Historical job tracking

---

## Architecture

### Technology Stack

- **Backend**: Flask 3.0.0 (Python web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: Bootstrap 5.1.3, Vanilla JavaScript
- **File Processing**: Pandas, openpyxl, xlrd
- **Migrations**: Flask-Migrate

### Application Structure

```
┌─────────────────────────────────────────┐
│           Flask Application             │
│              (app.py)                   │
├─────────────────────────────────────────┤
│  Blueprints:                            │
│  - journals_bp (USA/CA/AU)              │
│  - journals_eu_bp (EU/UK)              │
├─────────────────────────────────────────┤
│  Modules:                               │
│  - journal_generation/                  │
│    - journal_builder.py                 │
│    - journal_builder_eu.py              │
│    - journal_sync.py                      │
├─────────────────────────────────────────┤
│  Database Layer:                        │
│  - PostgreSQL                           │
│  - SQLAlchemy ORM                       │
│  - Flask-Migrate                        │
└─────────────────────────────────────────┘
```

---

## Project Structure

```
Permanent Reciepts/
├── app.py                          # Main Flask application (7000+ lines)
├── models.py                       # SQLAlchemy database models
├── config.py                       # Application configuration
├── journals_bp.py                  # USA/CA/AU Journals Processing Blueprint
├── journals_eu_bp.py               # EU/UK Journals Processing Blueprint
├── init_db.py                      # Database initialization script
├── init_subsidiaries.py            # Subsidiary data initialization
├── Start_App.command                # Application startup script (port 5001)
├── requirements.txt                # Python dependencies
├── env.example                     # Environment variables template
├── .env                           # Environment variables (not in repo)
├── .cursorrules                    # Development rules and guidelines
│
├── journal_generation/             # Journal generation modules
│   ├── journal_builder.py         # USA/CA/AU journal builder
│   ├── journal_builder_eu.py      # EU/UK journal builder
│   └── journal_sync.py            # Journal synchronization
│
├── migrations/                     # Database migrations
│   ├── versions/                   # Migration versions
│   └── env.py                      # Migration environment
│
├── templates/                      # HTML templates
│   ├── index.html                 # Dashboard
│   ├── receipts.html              # Job management
│   ├── reconciliation.html        # Main reconciliation page
│   ├── subsidiary_reconciliation.html
│   ├── reconciliation_process.html
│   ├── reconciliation_results.html
│   ├── journal_preparation.html
│   ├── journals_processing.html   # USA/CA/AU journals
│   ├── journals_processing_eu.html # EU/UK journals
│   ├── stripe_automation.html
│   ├── manual_payment_automation.html
│   ├── bacs_review.html
│   ├── looker_cashbook.html
│   └── ... (25 total templates)
│
├── static/                         # Static files
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js
│       └── receipts.js
│
├── uploads/                        # File upload directory
├── generated_journals/             # Generated journal files
│   ├── cross_sub_splits/          # Cross-subsidiary splits
│   ├── eu/                        # EU-specific journals
│   └── job_*_sub_*/               # Job-specific journals
│
└── README.md                       # This file
```

---

## Setup & Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package installer)

### Step 1: Clone/Download Project

```bash
cd "/Users/rahul/Documents/1 New Apps/mend/Permanent Reciepts"
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup PostgreSQL Database

#### Install PostgreSQL (if not already installed)

**macOS (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Create Database and User

```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql

# Create database and user
CREATE DATABASE receipts_dev;
CREATE USER receipts_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE receipts_dev TO receipts_user;
\q
```

### Step 5: Configure Environment Variables

```bash
# Copy the example environment file
cp env.example .env

# Edit .env file with your database credentials
nano .env  # or use your preferred editor
```

Update the following variables in `.env`:
```env
DEV_DATABASE_URL=postgresql://receipts_user:your_password@localhost:5432/receipts_dev
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True
```

### Step 6: Initialize Database

```bash
# Run the database initialization script
python init_db.py

# Initialize subsidiaries
python init_subsidiaries.py

# Initialize Flask migrations
flask db init

# Create initial migration (if needed)
flask db migrate -m "Initial migration"

# Apply migrations
flask db upgrade
```

### Step 7: Run the Application

**Option 1: Using Start_App.command (Recommended)**
```bash
# Make the script executable (first time only)
chmod +x Start_App.command

# Run the application
./Start_App.command
```

**Option 2: Manual Start**
```bash
python app.py
```

**Important Note**: The application runs on **port 5001** by default. The `Start_App.command` script automatically:
- Kills any existing Flask app running on port 5001
- Activates the virtual environment
- Starts the application

The application will be available at `http://localhost:5001`

### ⚠️ Important: Port 5001 Requirement

**The application MUST run on port 5001.** This is a hard requirement enforced by the application configuration.

**Using Start_App.command (Recommended):**
- The `Start_App.command` script automatically handles port cleanup
- It kills any existing process on port 5001 before starting
- Ensures a clean startup every time

**Manual Port Cleanup (if needed):**
```bash
# Kill any process on port 5001
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
```

**See `.cursorrules` file for development guidelines regarding port usage.**

---

## Configuration

### Environment Variables (.env)

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DEV_DATABASE_URL=postgresql://username:password@localhost:5432/receipts_dev
DATABASE_URL=postgresql://username:password@localhost:5432/receipts_prod

# File Processing Settings
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=16777216  # 16MB
PROCESSING_TIMEOUT=300  # 5 minutes

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Application Configuration (config.py)

- **Development**: Debug mode enabled, development database
- **Production**: Debug disabled, production database
- **Testing**: Test database configuration

---

## Database Models

The application uses SQLAlchemy ORM with the following main models:

### Core Models

1. **Receipt** - Receipt file information
2. **ProcessingJob** - Reconciliation job tracking
3. **Subsidiary** - Subsidiary information (AU, CA, US, EU, UK)

### Transaction Models

4. **StripeTransaction** - Stripe payment transactions
5. **CashbookTransaction** - Cashbook/bank statement entries
6. **LookerCashbookTransaction** - Looker cashbook data
7. **MatchedTransaction** - Matched transaction pairs
8. **ReconciliationResults** - Reconciliation process results

### Journal Models

9. **JournalTransaction** - Generated journal entries
10. **FPDataset** - File preparation dataset metadata
11. **FPJournalRow** - Original journal rows (immutable)
12. **FPWorkingRow** - Working copy of journal rows
13. **FPSummitInstallment** - Summit installment data
14. **FPProcessedJournal** - Processed journal entries
15. **FPMatchResult** - Matching results

### EU-Specific Models

16. **FPDatasetEU** - EU dataset metadata
17. **FPJournalRowEU** - EU journal rows
18. **FPSummitInstallmentEU** - EU summit installments
19. **FPMatchResultEU** - EU matching results
20. **FPProcessedJournalEU** - EU processed journals

### Automation Models

21. **StripeAutomationData** - Stripe automation input data
22. **StripeAutomationProcessed** - Processed Stripe automation
23. **StripeAutomationState** - Stripe automation state
24. **ManualPaymentOriginalCashbook** - Original cashbook for manual payments
25. **ManualPaymentOriginalBank** - Original bank data for manual payments
26. **ManualPaymentProcessedCashbook** - Processed cashbook
27. **ManualPaymentProcessedBank** - Processed bank data
28. **ManualPaymentState** - Manual payment state
29. **BacsReviewOriginal** - Original BACS review data
30. **BacsReviewProcessed** - Processed BACS review data
31. **BacsReviewState** - BACS review state

---

## Main Features & Workflows

### 1. Job Management

**Workflow:**
1. Create a new reconciliation job
2. Assign job name and description
3. Track job status (pending, running, completed, failed)
4. View job history and details

**Routes:**
- `/receipts` - Job management page
- `/api/jobs` - Create/list jobs
- `/api/jobs/<id>` - Job details
- `/job/<id>` - Job detail page

### 2. Reconciliation Process

**Workflow:**
1. Select job and subsidiary
2. Upload Stripe CSV file
3. Upload Cashbook Excel file
4. Start reconciliation process
5. Review matched/unmatched transactions
6. Generate journals

**Routes:**
- `/reconciliation/<job_id>` - Main reconciliation page
- `/reconciliation/<job_id>/<subsidiary_id>` - Subsidiary-specific page
- `/reconciliation-process/<job_id>/<subsidiary_id>` - Process page
- `/api/start-reconciliation/<job_id>/<subsidiary_id>` - Start reconciliation

**Matching Processes:**
- **Process 1**: Perfect matches (exact amount and date)
- **Process 2**: Date-amount matches (within tolerance)
- **Process 3**: Near matches (fuzzy matching)

### 3. Journal Generation

**Workflow:**
1. Complete reconciliation
2. Prepare journals (sync data)
3. Process summit installments (if applicable)
4. Generate journal files
5. Download journals

**Journal Types:**
- **Main Journal**: Primary transaction journal
- **POA Journal**: Proof of Account journal
- **Refunds Journal**: Refund transactions
- **Cross-Subsidiary Journal**: Cross-subsidiary splits
- **Salon Summit Installments**: Summit installment journal
- **Out of Cutoff**: Transactions outside cutoff period

**Routes:**
- `/journal-preparation/<job_id>/<subsidiary_id>` - Journal preparation
- `/api/journals/sync/<job_id>/<subsidiary_id>` - Sync journal data
- `/api/prepare-perfect-matches-journal/<job_id>/<subsidiary_id>` - Prepare perfect matches
- `/api/download-split-journals/<job_id>/<subsidiary_id>` - Download journals

### 4. Summit Installments Processing

**Workflow (USA/CA/AU):**
1. Upload journals to file preparation
2. Commit dataset
3. Load combined dataset
4. Upload Summit CSV file
5. Process installments
6. Download processed journals

**Workflow (EU/UK):**
1. Similar workflow with EU-specific processing

**Routes:**
- `/journals/` - Journals processing page (USA/CA/AU)
- `/journals-eu/` - Journals processing page (EU/UK)
- `/api/fp/summit-upload/<job_id>/<subsidiary_id>` - Upload summit data
- `/api/fp/summit-process/<job_id>/<subsidiary_id>` - Process installments

### 5. Stripe Automation

**Workflow:**
1. Upload Stripe automation CSV
2. Review original data
3. Process automation
4. Fix payment failures (if any)
5. Download processed file

**Routes:**
- `/stripe-automation/<job_id>` - Stripe automation page
- `/api/stripe-automation/upload/<job_id>` - Upload file
- `/api/stripe-automation/fix-payment-failures/<job_id>` - Fix failures

### 6. Manual Payment Automation

**Workflow:**
1. Upload cashbook and bank files
2. Inspect data
3. Process automation
4. Review processed data
5. Download results

**Routes:**
- `/manual-payment-automation/<job_id>` - Manual payment page
- `/api/manual-pay/upload/<job_id>` - Upload files
- `/api/manual-pay/process/<job_id>` - Process automation

### 7. BACS Review

**Workflow:**
1. Upload BACS review file
2. Process review
3. View processed data
4. Download results

**Routes:**
- `/bacs-review/<job_id>/<subsidiary_id>` - BACS review page
- `/api/bacs-review/upload/<job_id>/<subsidiary_id>` - Upload file
- `/api/bacs-review/process/<job_id>/<subsidiary_id>` - Process review

### 8. Looker Cashbook Integration

**Workflow:**
1. Upload Looker cashbook Excel file
2. Review transactions
3. Fix errors and locations
4. Fix bank accounts
5. Download corrected file

**Routes:**
- `/looker-cashbook/<job_id>` - Looker cashbook page
- `/api/looker-cashbook-upload/<job_id>` - Upload file
- `/api/looker-cashbook-fix-errors/<job_id>` - Fix errors

---

## API Endpoints

### Health & Status

- `GET /api/health` - Application health check

### Job Management

- `GET /api/jobs` - List all jobs
- `POST /api/jobs` - Create new job
- `GET /api/jobs/<id>` - Get job details
- `DELETE /api/jobs/<id>` - Delete job
- `POST /api/jobs/<id>/restart` - Restart job

### Subsidiary Management

- `GET /api/subsidiaries` - List all subsidiaries
- `POST /api/subsidiaries` - Create subsidiary

### File Upload

- `POST /api/upload` - Upload files
- `POST /api/stripe-upload/<job_id>/<subsidiary_id>` - Upload Stripe CSV
- `POST /api/cashbook-upload/<job_id>/<subsidiary_id>` - Upload cashbook Excel

### Reconciliation

- `POST /api/start-reconciliation/<job_id>/<subsidiary_id>` - Start reconciliation
- `POST /api/process1-match/<job_id>/<subsidiary_id>` - Process 1 matching
- `POST /api/process2-match/<job_id>/<subsidiary_id>` - Process 2 matching
- `POST /api/process3-match/<job_id>/<subsidiary_id>` - Process 3 matching
- `GET /api/matched-transactions-results/<job_id>/<subsidiary_id>` - Get results

### Journal Generation

- `POST /api/journals/sync/<job_id>/<subsidiary_id>` - Sync journal data
- `POST /api/prepare-perfect-matches-journal/<job_id>/<subsidiary_id>` - Prepare perfect matches
- `POST /api/prepare-date-amount-journal/<job_id>/<subsidiary_id>` - Prepare date-amount journal
- `GET /api/download-split-journals/<job_id>/<subsidiary_id>` - Download split journals
- `GET /api/download-refunds-journal/<job_id>/<subsidiary_id>` - Download refunds journal

### Summit Installments

- `POST /api/fp/summit-upload/<job_id>/<subsidiary_id>` - Upload summit data
- `POST /api/fp/summit-process/<job_id>/<subsidiary_id>` - Process installments
- `GET /api/fp/summit-status/<job_id>/<subsidiary_id>` - Get summit status

### Journals Processing (Blueprint)

- `GET /journals/` - Journals processing page
- `GET /journals/api/status/<job_id>/<subsidiary_id>` - Get status
- `POST /journals/api/upload-summit/<job_id>/<subsidiary_id>` - Upload summit
- `POST /journals/api/process/<job_id>/<subsidiary_id>` - Process installments
- `GET /journals/api/download/<job_id>/<subsidiary_id>/<journal_type>` - Download journal

### Automation Modules

- `POST /api/stripe-automation/upload/<job_id>` - Upload Stripe automation
- `POST /api/manual-pay/upload/<job_id>` - Upload manual payment files
- `POST /api/bacs-review/upload/<job_id>/<subsidiary_id>` - Upload BACS review

---

## How It Works

### Reconciliation Matching Logic

#### Process 1: Perfect Matches
- Matches transactions with **exact amount** and **exact date**
- Highest confidence level
- Used for primary journal generation

#### Process 2: Date-Amount Matches
- Matches transactions with **exact amount** but **date within tolerance** (default: 2 days)
- Medium confidence level
- Handles timing differences in bank processing

#### Process 3: Near Matches
- Fuzzy matching with **amount similarity** and **date within tolerance**
- Lower confidence level
- Requires manual review

### Journal Generation Process

1. **Data Collection**: Gather matched transactions from all processes
2. **Categorization**: Separate into Main, POA, Refunds, Cross-Subsidiary
3. **Summit Processing**: If summit installments exist, reduce amounts proportionally
4. **Journal Building**: Create journal entries with proper formatting
5. **Validation**: Verify totals match (original = processed + summit)
6. **Export**: Generate CSV/Excel files for download

### Summit Installments Processing

1. **Upload Summit Data**: CSV with OAK ID, Region, Installment Amount
2. **Match Clients**: Find matching client IDs in journal data
3. **Proportional Reduction**: Reduce journal amounts proportionally
4. **Create Summit Journal**: Generate new Salon_Summit_Installments journal
5. **Verification**: Ensure totals balance

### File Preparation System

1. **Upload Raw Files**: Excel/CSV files in various formats
2. **Data Extraction**: Parse and extract transaction data
3. **Validation**: Check for errors and missing data
4. **Conversion**: Convert to standard format
5. **Commit**: Save to database for processing

---

## Development

### Running in Development Mode

**Recommended: Use Start_App.command**
```bash
./Start_App.command
```

This script automatically:
- Closes any running application on port 5001
- Activates the virtual environment
- Starts the Flask app on port 5001

**Manual Start:**
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

**⚠️ Port Requirement**: The application MUST run on port 5001. Always ensure port 5001 is available before starting the application.

### Database Migrations

```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade
```

### Code Structure

- **app.py**: Main Flask application with all routes (7000+ lines)
- **models.py**: SQLAlchemy model definitions
- **journals_bp.py**: USA/CA/AU journals processing blueprint
- **journals_eu_bp.py**: EU/UK journals processing blueprint
- **journal_generation/**: Journal building modules

### Adding New Features

1. Create database migration if schema changes needed
2. Add models to `models.py` if new tables needed
3. Add routes to `app.py` or create new blueprint
4. Create templates in `templates/` directory
5. Update static files if UI changes needed

---

## Troubleshooting

### Common Issues

#### Database Connection Error
- **Solution**: Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists: `psql -U receipts_user -d receipts_dev`

#### Import Errors
- **Solution**: Activate virtual environment
- Install dependencies: `pip install -r requirements.txt`

#### File Upload Errors
- **Solution**: Check `uploads/` directory permissions
- Verify file size limits in `config.py`
- Check allowed file extensions

#### Migration Errors
- **Solution**: Check migration history: `flask db history`
- Rollback if needed: `flask db downgrade`
- Recreate migration: `flask db migrate -m "Fix migration"`

#### No Original Journals Found
- **Solution**: Go to "Further Processing" section
- Upload journals and commit dataset
- Load combined dataset before processing

#### Totals Don't Match
- **Cause**: Usually due to insufficient amounts or mismatched client IDs
- **Solution**: Review unmatched clients list
- Verify summit CSV data
- Check for data entry errors

### Logs

Check application logs:
- Console output (development mode)
- `server.log` file (if configured)
- Database query logs (if SQLALCHEMY_ECHO enabled)

### Debug Mode

Enable debug mode in `.env`:
```env
FLASK_DEBUG=True
FLASK_ENV=development
```

This will show detailed error messages and enable auto-reload.

---

## Additional Documentation

- **IMPLEMENTATION_DETAILS.md**: Detailed implementation documentation
- **JOURNALS_PROCESSING_README.md**: Journals processing workflow details

---

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Verify database connectivity
4. Ensure all prerequisites are installed
5. Check environment variables are set correctly

---

## License

[Add license information if applicable]

---

**Last Updated**: 2024
**Version**: 1.0
**Maintained By**: [Your Name/Team]
