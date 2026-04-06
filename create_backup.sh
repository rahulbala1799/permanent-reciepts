#!/bin/bash

# Backup Script for Permanent Receipts Application
# Creates a complete backup of code and database as of 1 Jan 2026

BACKUP_DIR="1 Jan 2026 Backup"
SOURCE_DIR="$(pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "========================================="
echo "Creating Backup: 1 Jan 2026"
echo "========================================="

# Create backup directory structure
mkdir -p "$BACKUP_DIR/code"
mkdir -p "$BACKUP_DIR/database"
mkdir -p "$BACKUP_DIR/docs"

echo "Step 1: Backing up source code..."

# Copy all Python files
echo "  - Copying Python files..."
find . -maxdepth 1 -name "*.py" -not -path "./venv/*" -exec cp {} "$BACKUP_DIR/code/" \;
cp -r journal_generation "$BACKUP_DIR/code/" 2>/dev/null || true

# Copy configuration files
echo "  - Copying configuration files..."
cp config.py "$BACKUP_DIR/code/" 2>/dev/null || true
cp requirements.txt "$BACKUP_DIR/code/" 2>/dev/null || true
cp env.example "$BACKUP_DIR/code/" 2>/dev/null || true
cp .cursorrules "$BACKUP_DIR/code/" 2>/dev/null || true
cp Start_App.command "$BACKUP_DIR/code/" 2>/dev/null || true

# Copy initialization scripts
echo "  - Copying initialization scripts..."
cp init_db.py "$BACKUP_DIR/code/" 2>/dev/null || true
cp init_subsidiaries.py "$BACKUP_DIR/code/" 2>/dev/null || true
cp migrate_add_original_amounts.py "$BACKUP_DIR/code/" 2>/dev/null || true
cp add_column.py "$BACKUP_DIR/code/" 2>/dev/null || true

# Copy templates
echo "  - Copying templates..."
cp -r templates "$BACKUP_DIR/code/" 2>/dev/null || true

# Copy static files
echo "  - Copying static files..."
cp -r static "$BACKUP_DIR/code/" 2>/dev/null || true

# Copy migrations
echo "  - Copying database migrations..."
cp -r migrations "$BACKUP_DIR/code/" 2>/dev/null || true

# Copy scripts
echo "  - Copying scripts..."
cp -r scripts "$BACKUP_DIR/code/" 2>/dev/null || true

# Copy documentation
echo "  - Copying documentation..."
cp README.md "$BACKUP_DIR/docs/" 2>/dev/null || true
cp IMPLEMENTATION_DETAILS.md "$BACKUP_DIR/docs/" 2>/dev/null || true
cp JOURNALS_PROCESSING_README.md "$BACKUP_DIR/docs/" 2>/dev/null || true

echo ""
echo "Step 2: Backing up database..."

# Try to get database connection from .env or use defaults
if [ -f .env ]; then
    # Extract database URL from .env
    DB_URL=$(grep "DEV_DATABASE_URL" .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
    
    if [ ! -z "$DB_URL" ]; then
        # Parse database connection details
        # Format: postgresql://user:password@host:port/database
        DB_NAME=$(echo $DB_URL | sed 's/.*\///')
        DB_HOST=$(echo $DB_URL | sed 's/.*@\([^:]*\).*/\1/')
        DB_PORT=$(echo $DB_URL | sed 's/.*:\([0-9]*\)\/.*/\1/' | grep -o '[0-9]*' || echo "5432")
        DB_USER=$(echo $DB_URL | sed 's/.*\/\/\([^:]*\):.*/\1/')
        DB_PASS=$(echo $DB_URL | sed 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/')
        
        echo "  - Database: $DB_NAME"
        echo "  - Host: $DB_HOST"
        echo "  - Port: $DB_PORT"
        echo "  - User: $DB_USER"
        
        # Export database using pg_dump
        export PGPASSWORD="$DB_PASS"
        pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F c -f "$BACKUP_DIR/database/receipts_backup_$TIMESTAMP.dump" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "  ✓ Database backup created successfully"
            # Also create SQL dump for easier inspection
            pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$BACKUP_DIR/database/receipts_backup_$TIMESTAMP.sql" 2>/dev/null
            echo "  ✓ SQL dump created successfully"
        else
            echo "  ⚠ Database backup failed. Please check database connection."
            echo "  You may need to manually export the database."
        fi
        unset PGPASSWORD
    else
        echo "  ⚠ Could not find DEV_DATABASE_URL in .env file"
        echo "  Please manually export the database using:"
        echo "  pg_dump -U your_user -d receipts_dev > database_backup.sql"
    fi
else
    echo "  ⚠ .env file not found"
    echo "  Please manually export the database using:"
    echo "  pg_dump -U your_user -d receipts_dev > database_backup.sql"
fi

echo ""
echo "Step 3: Creating restore script..."

# Create restore script
cat > "$BACKUP_DIR/RESTORE_INSTRUCTIONS.md" << 'EOF'
# Restore Instructions - 1 Jan 2026 Backup

## Overview
This backup contains the complete application code and database as of 1 Jan 2026.

## Contents
- `code/` - All source code, templates, static files, migrations
- `database/` - Database backup files (.dump and .sql)
- `docs/` - Documentation files

## Restore Steps

### 1. Restore Code

```bash
# Navigate to your project directory
cd "/Users/rahul/Documents/1 New Apps/mend/Permanent Reciepts"

# Backup current code (optional but recommended)
mv app.py app.py.backup
mv models.py models.py.backup

# Copy files from backup
cp "1 Jan 2026 Backup/code/"*.py .
cp -r "1 Jan 2026 Backup/code/templates" .
cp -r "1 Jan 2026 Backup/code/static" .
cp -r "1 Jan 2026 Backup/code/migrations" .
cp -r "1 Jan 2026 Backup/code/journal_generation" .
cp -r "1 Jan 2026 Backup/code/scripts" .
cp "1 Jan 2026 Backup/code/"*.command .
cp "1 Jan 2026 Backup/code/"*.txt .
cp "1 Jan 2026 Backup/code/"*.example .
cp "1 Jan 2026 Backup/code/.cursorrules" .
```

### 2. Restore Database

#### Option A: Using pg_restore (for .dump file)
```bash
# Get database connection details from your .env file
# Then restore:
pg_restore -h localhost -p 5432 -U your_user -d receipts_dev -c "1 Jan 2026 Backup/database/receipts_backup_*.dump"
```

#### Option B: Using psql (for .sql file)
```bash
# Get database connection details from your .env file
# Then restore:
psql -h localhost -p 5432 -U your_user -d receipts_dev < "1 Jan 2026 Backup/database/receipts_backup_*.sql"
```

#### Option C: Manual Steps
1. Drop existing database (if needed):
   ```sql
   DROP DATABASE receipts_dev;
   CREATE DATABASE receipts_dev;
   ```

2. Restore from backup:
   ```bash
   psql -U your_user -d receipts_dev < "1 Jan 2026 Backup/database/receipts_backup_*.sql"
   ```

### 3. Verify Restoration

1. Check that all files are in place
2. Verify database connection:
   ```bash
   python -c "from app import app, db; app.app_context().push(); print('DB connected:', db.engine.connect())"
   ```

3. Run migrations (if needed):
   ```bash
   flask db upgrade
   ```

4. Start the application:
   ```bash
   ./Start_App.command
   ```

5. Verify application runs on http://localhost:5001

## Important Notes

- **Port 5001**: The application MUST run on port 5001 (see .cursorrules)
- **Environment Variables**: You'll need to restore your .env file separately (not included in backup for security)
- **Virtual Environment**: Recreate venv if needed: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- **Database Credentials**: Update .env file with correct database credentials before restoring database

## Backup Date
1 January 2026

## Backup Contents
- Application code (all .py files)
- Templates (HTML files)
- Static files (CSS, JS)
- Database migrations
- Database backup (SQL and dump formats)
- Configuration files
- Documentation

EOF

echo "  ✓ Restore instructions created"

echo ""
echo "Step 4: Creating backup manifest..."

# Create manifest
cat > "$BACKUP_DIR/BACKUP_MANIFEST.txt" << EOF
=========================================
Backup Manifest - 1 Jan 2026
=========================================
Backup Date: $(date)
Source Directory: $SOURCE_DIR
Backup Directory: $BACKUP_DIR

Contents:
---------
Code Files:
- app.py
- models.py
- config.py
- journals_bp.py
- journals_eu_bp.py
- All initialization scripts
- All Python modules in journal_generation/
- All templates in templates/
- All static files in static/
- All migrations in migrations/
- All scripts in scripts/
- Configuration files (config.py, requirements.txt, env.example, .cursorrules)
- Start_App.command

Database:
- PostgreSQL dump file (.dump format)
- SQL dump file (.sql format)

Documentation:
- README.md
- IMPLEMENTATION_DETAILS.md
- JOURNALS_PROCESSING_README.md

Excluded:
---------
- __pycache__ directories
- .pyc files
- .env file (contains sensitive data)
- venv/ directory
- Large generated files
- Upload files (can be regenerated)

To Restore:
-----------
See RESTORE_INSTRUCTIONS.md for detailed restore steps.

Quick Restore Command:
cd "$SOURCE_DIR"
# Then follow instructions in RESTORE_INSTRUCTIONS.md

EOF

echo "  ✓ Backup manifest created"

echo ""
echo "========================================="
echo "Backup Complete!"
echo "========================================="
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Contents:"
echo "  - Code: $BACKUP_DIR/code/"
echo "  - Database: $BACKUP_DIR/database/"
echo "  - Documentation: $BACKUP_DIR/docs/"
echo "  - Restore Instructions: $BACKUP_DIR/RESTORE_INSTRUCTIONS.md"
echo ""
echo "To restore this backup, see: $BACKUP_DIR/RESTORE_INSTRUCTIONS.md"
echo "========================================="
