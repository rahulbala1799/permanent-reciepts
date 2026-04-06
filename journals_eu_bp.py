"""
EU-SPECIFIC Journals Processing Blueprint
Completely separate from USA - uses EU-specific tables only
Works with 1-8 journal files flexibly
"""

from flask import Blueprint, render_template, request, jsonify, send_file
from datetime import datetime
import json
import csv
import os

journals_eu_bp = Blueprint('journals_eu', __name__, url_prefix='/journals-eu')

# Will be initialized by app.py
db = None
models = {}

def init_blueprint(database, eu_models):
    """Initialize blueprint with database and EU models"""
    global db, models
    db = database
    models = eu_models

@journals_eu_bp.route('/')
def index():
    """EU Journals Processing Page"""
    job_id = request.args.get('job_id', 1, type=int)
    return render_template('journals_processing_eu.html', job_id=job_id)

@journals_eu_bp.route('/api/status/<int:job_id>')
def get_status(job_id):
    """Get EU processing status"""
    try:
        FPDatasetEU = models['FPDatasetEU']
        FPJournalRowEU = models['FPJournalRowEU']
        FPSummitInstallmentEU = models['FPSummitInstallmentEU']
        FPMatchResultEU = models['FPMatchResultEU']
        FPProcessedJournalEU = models['FPProcessedJournalEU']
        
        dataset = FPDatasetEU.query.filter_by(job_id=job_id).first()
        
        if not dataset:
            return jsonify({
                'success': True,
                'dataset_loaded': False,
                'journals_uploaded': [],
                'summit_uploaded': False,
                'match_complete': False,
                'processing_complete': False
            })
        
        # Check which journals are uploaded
        uploaded_types = db.session.query(FPJournalRowEU.journal_type).filter_by(
            dataset_id=dataset.id
        ).distinct().all()
        uploaded_list = [t[0] for t in uploaded_types]
        
        # Get counts for each type
        journal_counts = {}
        journal_totals = {}
        for jtype in uploaded_list:
            count = FPJournalRowEU.query.filter_by(dataset_id=dataset.id, journal_type=jtype).count()
            total = db.session.query(db.func.sum(FPJournalRowEU.amount)).filter_by(
                dataset_id=dataset.id, journal_type=jtype
            ).scalar() or 0
            journal_counts[jtype] = count
            journal_totals[jtype] = round(float(total), 2)
        
        # Check summit
        summit_count = FPSummitInstallmentEU.query.filter_by(dataset_id=dataset.id).count()
        
        # Check matches
        match_count = FPMatchResultEU.query.filter_by(dataset_id=dataset.id).count()
        
        # Check processed
        processed_count = FPProcessedJournalEU.query.filter_by(dataset_id=dataset.id).count()
        
        return jsonify({
            'success': True,
            'dataset_loaded': len(uploaded_list) > 0,
            'journals_uploaded': uploaded_list,
            'journal_counts': journal_counts,
            'journal_totals': journal_totals,
            'summit_uploaded': summit_count > 0,
            'summit_count': summit_count,
            'match_complete': match_count > 0,
            'match_count': match_count,
            'processing_complete': processed_count > 0
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@journals_eu_bp.route('/api/upload-journals/<int:job_id>', methods=['POST'])
def upload_journals(job_id):
    """Upload EU journal files - flexible, accepts any of the 8 types"""
    try:
        FPDatasetEU = models['FPDatasetEU']
        FPJournalRowEU = models['FPJournalRowEU']
        
        # Get or create dataset
        dataset = FPDatasetEU.query.filter_by(job_id=job_id).first()
        if not dataset:
            dataset = FPDatasetEU(job_id=job_id, status='loaded')
            db.session.add(dataset)
            db.session.flush()
        
        payload = request.get_json(force=True)
        journal_type = payload.get('journal_type')
        filename = payload.get('filename', 'uploaded.csv')
        rows = payload.get('rows', [])
        
        # Valid EU journal types
        valid_types = ['Main_EU', 'POA_EU', 'Cross_Subsidiary_EU', 'Refunds_EU',
                      'Main_AED', 'POA_AED', 'Cross_Subsidiary_AED', 'Refunds_AED']
        
        if journal_type not in valid_types:
            return jsonify({'success': False, 'error': f'Invalid journal_type: {journal_type}'}), 400
        
        # Check if already uploaded
        existing = FPJournalRowEU.query.filter_by(dataset_id=dataset.id, journal_type=journal_type).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f'{journal_type} already uploaded. Clear to re-upload.'
            }), 409
        
        # Store rows
        created = 0
        for row in rows:
            amount = float(row.get('amount', 0) or 0)
            client_id = str(row.get('client_id') or row.get('Client') or '')
            invoice_number = str(row.get('invoice_number') or row.get('Invoice') or '')
            
            journal_row = FPJournalRowEU(
                dataset_id=dataset.id,
                job_id=job_id,
                journal_type=journal_type,
                client_id=client_id,
                invoice_number=invoice_number,
                amount=amount,
                row_json=json.dumps(row),
                filename=filename
            )
            db.session.add(journal_row)
            created += 1
        
        # Mark as committed if ANY journals uploaded
        dataset.status = 'committed'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'created': created,
            'journal_type': journal_type
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@journals_eu_bp.route('/api/upload-summit/<int:job_id>', methods=['POST'])
def upload_summit(job_id):
    """Upload summit installments CSV"""
    try:
        FPDatasetEU = models['FPDatasetEU']
        FPSummitInstallmentEU = models['FPSummitInstallmentEU']
        FPJournalRowEU = models['FPJournalRowEU']
        
        dataset = FPDatasetEU.query.filter_by(job_id=job_id).first()
        if not dataset:
            return jsonify({'success': False, 'error': 'Please upload at least one journal file first'}), 400
        
        # Check if at least one journal uploaded
        journal_count = FPJournalRowEU.query.filter_by(dataset_id=dataset.id).count()
        if journal_count == 0:
            return jsonify({'success': False, 'error': 'Please upload at least one journal file first'}), 400
        
        # Check if already uploaded
        existing = FPSummitInstallmentEU.query.filter_by(dataset_id=dataset.id).first()
        if existing:
            return jsonify({'success': False, 'error': 'Summit data already uploaded. Clear to re-upload.'}), 409
        
        payload = request.get_json(force=True)
        summit_data = payload.get('summit_data', [])
        
        if not summit_data:
            return jsonify({'success': False, 'error': 'No summit data provided'}), 400
        
        # Store summit data
        uploaded_count = 0
        for item in summit_data:
            client_id = str(item.get('oak_id', '')).strip()
            region = str(item.get('region', '')).strip()
            installment_amount = float(item.get('installment_amount', 0))
            
            if client_id and installment_amount != 0:
                installment = FPSummitInstallmentEU(
                    dataset_id=dataset.id,
                    job_id=job_id,
                    client_id=client_id,
                    region=region,
                    installment_amount=installment_amount
                )
                db.session.add(installment)
                uploaded_count += 1
        
        db.session.commit()
        
        return jsonify({'success': True, 'uploaded_count': uploaded_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@journals_eu_bp.route('/api/match-summit/<int:job_id>', methods=['POST'])
def match_summit(job_id):
    """Match summit installments with uploaded journals"""
    try:
        FPDatasetEU = models['FPDatasetEU']
        FPJournalRowEU = models['FPJournalRowEU']
        FPSummitInstallmentEU = models['FPSummitInstallmentEU']
        FPMatchResultEU = models['FPMatchResultEU']
        
        dataset = FPDatasetEU.query.filter_by(job_id=job_id).first()
        if not dataset:
            return jsonify({'success': False, 'error': 'Please upload journals first'}), 400
        
        # Check journals uploaded
        journal_count = FPJournalRowEU.query.filter_by(dataset_id=dataset.id).count()
        if journal_count == 0:
            return jsonify({'success': False, 'error': 'Please upload journals first'}), 400
        
        # Check summit uploaded
        summit_installments = FPSummitInstallmentEU.query.filter_by(dataset_id=dataset.id).all()
        if not summit_installments:
            return jsonify({'success': False, 'error': 'No summit data uploaded'}), 400
        
        # Check if already matched
        existing_matches = FPMatchResultEU.query.filter_by(dataset_id=dataset.id).first()
        if existing_matches:
            return jsonify({'success': False, 'error': 'Already matched. Clear to re-match.'}), 409
        
        # Build lookup from journals
        journal_rows = FPJournalRowEU.query.filter_by(dataset_id=dataset.id).all()
        client_amounts = {}
        for row in journal_rows:
            client_id = str(row.client_id).strip() if row.client_id else ''
            if client_id:
                if client_id not in client_amounts:
                    client_amounts[client_id] = 0
                client_amounts[client_id] += (row.amount or 0)
        
        # Combine duplicate summit clients
        summit_by_client = {}
        for inst in summit_installments:
            client_id = inst.client_id.strip()
            if client_id not in summit_by_client:
                summit_by_client[client_id] = 0
            summit_by_client[client_id] += inst.installment_amount
        
        # Match
        matched_count = 0
        insufficient_count = 0
        unmatched_count = 0
        
        for client_id, installment_amount in summit_by_client.items():
            if client_id not in client_amounts:
                # Unmatched
                match_result = FPMatchResultEU(
                    dataset_id=dataset.id,
                    job_id=job_id,
                    client_id=client_id,
                    match_status='unmatched',
                    total_received=0,
                    installment_amount=installment_amount,
                    remaining_amount=0
                )
                unmatched_count += 1
            else:
                total_received = client_amounts[client_id]
                if total_received < installment_amount:
                    # Insufficient
                    match_result = FPMatchResultEU(
                        dataset_id=dataset.id,
                        job_id=job_id,
                        client_id=client_id,
                        match_status='insufficient',
                        total_received=total_received,
                        installment_amount=installment_amount,
                        remaining_amount=total_received - installment_amount
                    )
                    insufficient_count += 1
                else:
                    # Matched
                    match_result = FPMatchResultEU(
                        dataset_id=dataset.id,
                        job_id=job_id,
                        client_id=client_id,
                        match_status='matched',
                        total_received=total_received,
                        installment_amount=installment_amount,
                        remaining_amount=total_received - installment_amount
                    )
                    matched_count += 1
            
            db.session.add(match_result)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'matched_count': matched_count,
            'insufficient_count': insufficient_count,
            'unmatched_count': unmatched_count,
            'message': f'✅ Matched {matched_count} clients'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@journals_eu_bp.route('/api/generate-journals/<int:job_id>', methods=['POST'])
def generate_journals(job_id):
    """Generate split journals using JournalBuilderEU - EXACT same logic as USA"""
    try:
        FPDatasetEU = models['FPDatasetEU']
        FPMatchResultEU = models['FPMatchResultEU']
        FPProcessedJournalEU = models['FPProcessedJournalEU']
        
        dataset = FPDatasetEU.query.filter_by(job_id=job_id).first()
        if not dataset:
            return jsonify({'success': False, 'error': 'No dataset found'}), 400
        
        # Check matches exist
        matches = FPMatchResultEU.query.filter_by(dataset_id=dataset.id, match_status='matched').all()
        if not matches:
            return jsonify({'success': False, 'error': 'Please match summit data first'}), 400
        
        # Delete existing processed journals if any (allow regeneration)
        FPProcessedJournalEU.query.filter_by(dataset_id=dataset.id).delete()
        db.session.commit()
        
        # Get all journal rows - NO PANDAS, just plain Python
        FPJournalRowEU = models['FPJournalRowEU']
        rows = FPJournalRowEU.query.filter_by(dataset_id=dataset.id).all()
        
        # Parse all rows into dict format
        journal_data = {}  # {journal_type: [rows]}
        for row in rows:
            if row.row_json:
                try:
                    row_dict = json.loads(row.row_json)
                    jtype = row.journal_type
                    if jtype not in journal_data:
                        journal_data[jtype] = []
                    journal_data[jtype].append(row_dict)
                except:
                    pass
        
        # Build match lookup for installments
        installments = {}
        for match in matches:
            installments[match.client_id] = float(match.installment_amount)
        
        # Track which clients we've already reduced (so we only reduce once per client)
        processed_clients = set()
        
        # Process each journal type separately
        generated_files = []
        for jtype, rows_list in journal_data.items():
            total_amount = 0
            
            for row_dict in rows_list:
                client_id = str(row_dict.get('client_id', '')).strip()
                
                # Apply installment reduction if this client matches AND we haven't processed them yet
                if client_id in installments and client_id not in processed_clients:
                    original_amount = float(row_dict.get('amount', 0))
                    reduction = installments[client_id]
                    new_amount = max(0, original_amount - reduction)
                    row_dict['amount'] = new_amount
                    # Mark as processed so we don't reduce again
                    processed_clients.add(client_id)
                
                # Fix account for Germany billing entities (applies to ALL journals)
                billing_entity = row_dict.get('billing_entity', '')
                if 'Phorest Germany' in billing_entity:
                    row_dict['account'] = '10010c Bank : Dummy Interco Bank Accounts : Interco - BOI current a/c \u00C4 # 17013705 (Germany)'  # Ä = U+00C4
                # Add more country mappings here if needed
                
                # Save to FPProcessedJournalEU
                processed = FPProcessedJournalEU(
                    dataset_id=dataset.id,
                    job_id=job_id,
                    journal_type=jtype,
                    client_id=str(row_dict.get('client_id', '')),
                    invoice_number=str(row_dict.get('invoice_number', '')),
                    amount=float(row_dict.get('amount', 0)),
                    row_json=json.dumps(row_dict, ensure_ascii=False)
                )
                db.session.add(processed)
                total_amount += float(row_dict.get('amount', 0))
            
            generated_files.append({
                'journal_type': jtype,
                'row_count': len(rows_list),
                'total_amount': round(total_amount, 2)
            })
        
        # Create Summit installments journal (for any remaining installments that weren't applied)
        if installments:
            summit_total = 0
            summit_count = 0
            for client_id, installment in installments.items():
                # Find ANY row for this client to copy structure
                client_row = None
                original_billing_entity = None
                for jtype, rows_list in journal_data.items():
                    for row_dict in rows_list:
                        if str(row_dict.get('client_id', '')).strip() == client_id:
                            client_row = row_dict.copy()
                            original_billing_entity = row_dict.get('billing_entity', '')
                            break
                    if client_row:
                        break
                
                if client_row:
                    client_row['amount'] = installment
                    
                    # ALWAYS set billing entity to Ireland for Summit journals
                    client_row['billing_entity'] = 'Ndevor Systems Ltd : Phorest Ireland'
                    
                    # Set account (bank) based on ORIGINAL billing entity and currency
                    # Using EXACT strings from uploaded data with correct special characters
                    if 'Germany' in original_billing_entity:
                        client_row['account'] = '10010c Bank : Dummy Interco Bank Accounts : Interco - BOI current a/c \u00C4 # 17013705 (Germany)'  # Ä = U+00C4
                    elif client_row.get('currency') == 'USD':
                        client_row['account'] = '10040a Bank : Dummy Interco Bank Accounts : Interco - SVB current a/c # 5468 & CIBC # 5090'
                    elif client_row.get('currency') == 'GBP':
                        client_row['account'] = '10020a Bank : Dummy Interco Bank Accounts : Interco - BOI current a/c \u00A3 # 62100285'  # £ = U+00A3
                    # Add more country mappings if needed (Austria, France, etc.)
                    # Keep original account if no specific mapping
                    
                    processed = FPProcessedJournalEU(
                        dataset_id=dataset.id,
                        job_id=job_id,
                        journal_type='Salon_Summit_Installments',
                        client_id=client_id,
                        invoice_number=client_row.get('invoice_number', ''),
                        amount=installment,
                        row_json=json.dumps(client_row, ensure_ascii=False)
                    )
                    db.session.add(processed)
                    summit_total += installment
                    summit_count += 1
            
            if summit_count > 0:
                generated_files.append({
                    'journal_type': 'Salon_Summit_Installments',
                    'row_count': summit_count,
                    'total_amount': round(summit_total, 2)
                })
        
        db.session.commit()
        
        # Calculate reconciliation
        # Original total from uploaded journals
        original_rows = FPJournalRowEU.query.filter_by(dataset_id=dataset.id).all()
        original_total = sum(float(row.amount or 0) for row in original_rows)
        
        # New total from generated journals
        processed_rows = FPProcessedJournalEU.query.filter_by(dataset_id=dataset.id).all()
        new_total = sum(float(row.amount or 0) for row in processed_rows)
        
        # Build breakdown by journal type
        original_breakdown = {}
        for row in original_rows:
            jtype = row.journal_type
            if jtype not in original_breakdown:
                original_breakdown[jtype] = 0
            original_breakdown[jtype] += float(row.amount or 0)
        
        new_breakdown = {}
        for row in processed_rows:
            jtype = row.journal_type
            if jtype not in new_breakdown:
                new_breakdown[jtype] = 0
            new_breakdown[jtype] += float(row.amount or 0)
        
        difference = abs(original_total - new_total)
        balanced = difference < 0.01  # Allow 1 cent difference for rounding
        
        return jsonify({
            'success': True,
            'message': f'✅ Generated {len(generated_files)} journals',
            'generated_files': generated_files,
            'reconciliation': {
                'original_total': round(original_total, 2),
                'new_total': round(new_total, 2),
                'difference': round(difference, 2),
                'balanced': balanced,
                'original_breakdown': {k: round(v, 2) for k, v in original_breakdown.items()},
                'new_breakdown': {k: round(v, 2) for k, v in new_breakdown.items()}
            }
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"ERROR: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@journals_eu_bp.route('/api/download/<int:job_id>/<journal_type>')
def download_journal(job_id, journal_type):
    """Download a processed journal as CSV with optional memo"""
    try:
        FPDatasetEU = models['FPDatasetEU']
        FPProcessedJournalEU = models['FPProcessedJournalEU']
        
        # Get memo from query parameter
        memo = request.args.get('memo', '')
        
        dataset = FPDatasetEU.query.filter_by(job_id=job_id).first()
        if not dataset:
            return jsonify({'success': False, 'error': 'No dataset found'}), 404
        
        rows = FPProcessedJournalEU.query.filter_by(
            dataset_id=dataset.id,
            journal_type=journal_type
        ).all()
        
        if not rows:
            return jsonify({'success': False, 'error': f'No rows found for {journal_type}'}), 404
        
        # Create CSV
        output_dir = 'generated_journals/eu'
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{journal_type}_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Define the EXACT headers expected for all journals (universal format)
        headers = [
            'payment_date', 'client_id', 'invoice_number', 'billing_entity', 'ar_account',
            'currency', 'exchange_rate', 'amount', 'account', 'Location', 'transtype',
            'comment', 'Card Reference', 'reasoncode', 'sepaprovider', 'invoice #', 'payment #', 'Memo'
        ]
        
        # Write CSV with cp1252 so Ä, £ etc. display correctly in Excel/NetSuite (EU only)
        with open(filepath, 'w', newline='', encoding='cp1252', errors='replace') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            
            for row in rows:
                if row.row_json:
                    try:
                        # Ensure proper UTF-8 decoding
                        if isinstance(row.row_json, bytes):
                            row_data = json.loads(row.row_json.decode('utf-8'))
                        else:
                            row_data = json.loads(row.row_json, strict=False)
                        # Update amount with the processed amount (after installment reduction)
                        row_data['amount'] = str(row.amount)
                        
                        # Map columns to expected names (if they have different names in uploaded data)
                        output_row = {}
                        for header in headers:
                            # Handle case-sensitive mapping
                            if header == 'Location':
                                output_row['Location'] = row_data.get('location', row_data.get('Location', ''))
                            elif header == 'Card Reference':
                                output_row['Card Reference'] = row_data.get('card_reference', row_data.get('Card Reference', ''))
                            elif header == 'Memo':
                                # Use the memo parameter if provided, otherwise use original
                                output_row['Memo'] = memo if memo else row_data.get('memo', row_data.get('Memo', ''))
                            elif header == 'invoice #':
                                # ALWAYS regenerate invoice # - don't use old values with 'nan'
                                client_id = row_data.get('client_id', '')
                                invoice_num = row_data.get('invoice_number', '')
                                if client_id and invoice_num and client_id != 'nan' and invoice_num != 'nan':
                                    invoice_hash = f"CPMT: {client_id}-{invoice_num}"
                                    # Append "-Summit" for Salon Summit journals
                                    if journal_type == 'Salon_Summit_Installments':
                                        invoice_hash += '-Summit'
                                    output_row['invoice #'] = invoice_hash
                                else:
                                    output_row['invoice #'] = ''
                            elif header == 'payment #':
                                # ALWAYS regenerate payment # - don't use old values with 'nan'
                                client_id = row_data.get('client_id', '')
                                invoice_num = row_data.get('invoice_number', '')
                                payment_date = row_data.get('payment_date', '')
                                if client_id and invoice_num and payment_date and client_id != 'nan' and invoice_num != 'nan' and payment_date != 'nan':
                                    payment_hash = f"CPMT: {client_id}-{invoice_num}-{payment_date}"
                                    # Append "-Summit" for Salon Summit journals
                                    if journal_type == 'Salon_Summit_Installments':
                                        payment_hash += '-Summit'
                                    output_row['payment #'] = payment_hash
                                else:
                                    output_row['payment #'] = ''
                            else:
                                output_row[header] = row_data.get(header, '')
                        
                        writer.writerow(output_row)
                    except Exception as e:
                        print(f"Error writing row: {e}")
                        continue
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@journals_eu_bp.route('/api/download-all/<int:job_id>')
def download_all_journals(job_id):
    """Download all generated journals as a ZIP file with optional memo"""
    import zipfile
    import io
    
    try:
        FPDatasetEU = models['FPDatasetEU']
        FPProcessedJournalEU = models['FPProcessedJournalEU']
        
        dataset = FPDatasetEU.query.filter_by(job_id=job_id).first()
        if not dataset:
            return jsonify({'success': False, 'error': 'No dataset found'}), 404
        
        # Get memo parameter
        memo = request.args.get('memo', '').strip()
        
        # Get all unique journal types
        journal_types = db.session.query(FPProcessedJournalEU.journal_type).filter_by(
            dataset_id=dataset.id
        ).distinct().all()
        
        if not journal_types:
            return jsonify({'success': False, 'error': 'No generated journals found'}), 404
        
        # Create ZIP in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for (jtype,) in journal_types:
                # Generate CSV for each journal type
                rows = FPProcessedJournalEU.query.filter_by(
                    dataset_id=dataset.id,
                    journal_type=jtype
                ).all()
                
                if not rows:
                    continue
                
                # Define expected columns
                headers = [
                    'payment_date', 'client_id', 'invoice_number', 'billing_entity', 'ar_account',
                    'currency', 'exchange_rate', 'amount', 'account', 'Location', 'transtype',
                    'comment', 'Card Reference', 'reasoncode', 'sepaprovider', 'invoice #', 'payment #', 'Memo'
                ]
                
                # Create CSV content
                csv_content = io.StringIO()
                writer = csv.DictWriter(csv_content, fieldnames=headers, extrasaction='ignore')
                writer.writeheader()
                
                for row in rows:
                    if row.row_json:
                        try:
                            if isinstance(row.row_json, bytes):
                                row_data = json.loads(row.row_json.decode('utf-8'))
                            else:
                                row_data = json.loads(row.row_json, strict=False)
                            
                            row_data['amount'] = str(row.amount)
                            
                            # Build output row with proper column mapping
                            output_row = {}
                            for header in headers:
                                if header == 'Location':
                                    output_row['Location'] = row_data.get('location', row_data.get('Location', ''))
                                elif header == 'Card Reference':
                                    output_row['Card Reference'] = row_data.get('card_reference', row_data.get('Card Reference', ''))
                                elif header == 'Memo':
                                    output_row['Memo'] = memo if memo else row_data.get('memo', row_data.get('Memo', ''))
                                elif header == 'invoice #':
                                    client_id = row_data.get('client_id', '')
                                    invoice_num = row_data.get('invoice_number', '')
                                    if client_id and invoice_num and client_id != 'nan' and invoice_num != 'nan':
                                        invoice_hash = f"CPMT: {client_id}-{invoice_num}"
                                        if jtype == 'Salon_Summit_Installments':
                                            invoice_hash += '-Summit'
                                        output_row['invoice #'] = invoice_hash
                                    else:
                                        output_row['invoice #'] = ''
                                elif header == 'payment #':
                                    client_id = row_data.get('client_id', '')
                                    invoice_num = row_data.get('invoice_number', '')
                                    payment_date = row_data.get('payment_date', '')
                                    if client_id and invoice_num and payment_date and client_id != 'nan' and invoice_num != 'nan' and payment_date != 'nan':
                                        payment_hash = f"CPMT: {client_id}-{invoice_num}-{payment_date}"
                                        if jtype == 'Salon_Summit_Installments':
                                            payment_hash += '-Summit'
                                        output_row['payment #'] = payment_hash
                                    else:
                                        output_row['payment #'] = ''
                                else:
                                    output_row[header] = row_data.get(header, '')
                            
                            writer.writerow(output_row)
                        except Exception as e:
                            print(f"Error writing row: {e}")
                            continue
                
                # Add CSV to ZIP – use cp1252 so Ä, £ etc. display correctly in Excel/NetSuite (EU only)
                csv_bytes = csv_content.getvalue().encode('cp1252', errors='replace')
                zf.writestr(f"{jtype}.csv", csv_bytes)
        
        memory_file.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'EU_Journals_{job_id}_{timestamp}.zip'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@journals_eu_bp.route('/api/clear/<int:job_id>', methods=['DELETE'])
def clear_all(job_id):
    """Clear all EU data for this job"""
    try:
        FPDatasetEU = models['FPDatasetEU']
        FPJournalRowEU = models['FPJournalRowEU']
        FPSummitInstallmentEU = models['FPSummitInstallmentEU']
        FPMatchResultEU = models['FPMatchResultEU']
        FPProcessedJournalEU = models['FPProcessedJournalEU']
        
        dataset = FPDatasetEU.query.filter_by(job_id=job_id).first()
        if not dataset:
            return jsonify({'success': True, 'message': 'No data to clear'})
        
        # Delete all related data
        FPProcessedJournalEU.query.filter_by(dataset_id=dataset.id).delete()
        FPMatchResultEU.query.filter_by(dataset_id=dataset.id).delete()
        FPSummitInstallmentEU.query.filter_by(dataset_id=dataset.id).delete()
        FPJournalRowEU.query.filter_by(dataset_id=dataset.id).delete()
        db.session.delete(dataset)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'All EU data cleared'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@journals_eu_bp.route('/api/journals-upload-status/<int:job_id>')
def journals_upload_status(job_id):
    """Get upload status for EU journals"""
    try:
        FPDatasetEU = models['FPDatasetEU']
        FPJournalRowEU = models['FPJournalRowEU']
        
        dataset = FPDatasetEU.query.filter_by(job_id=job_id).first()
        
        journal_types = ['Main_EU', 'POA_EU', 'Cross_Subsidiary_EU', 'Refunds_EU',
                        'Main_AED', 'POA_AED', 'Cross_Subsidiary_AED', 'Refunds_AED']
        
        if not dataset:
            return jsonify({
                'success': True,
                'uploaded': {jtype: False for jtype in journal_types},
                'counts': {},
                'totals': {},
                'all_uploaded': False
            })
        
        uploaded = {}
        counts = {}
        totals = {}
        
        for jtype in journal_types:
            count = FPJournalRowEU.query.filter_by(dataset_id=dataset.id, journal_type=jtype).count()
            total = db.session.query(db.func.sum(FPJournalRowEU.amount)).filter_by(
                dataset_id=dataset.id, journal_type=jtype
            ).scalar() or 0
            
            uploaded[jtype] = count > 0
            counts[jtype] = count
            totals[jtype] = round(float(total), 2)
        
        # Consider "all uploaded" if at least ONE is uploaded (flexible)
        any_uploaded = any(uploaded.values())
        
        return jsonify({
            'success': True,
            'uploaded': uploaded,
            'counts': counts,
            'totals': totals,
            'all_uploaded': any_uploaded,
            'dataset_status': dataset.status if dataset else None
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@journals_eu_bp.route('/view-data/<int:job_id>')
def view_combined_data(job_id):
    """View combined EU journal data"""
    try:
        FPDatasetEU = models['FPDatasetEU']
        FPJournalRowEU = models['FPJournalRowEU']
        
        dataset = FPDatasetEU.query.filter_by(job_id=job_id).first()
        if not dataset:
            return render_template('error.html', 
                message='No EU dataset found for this job',
                back_url=f'/journals-eu/?job_id={job_id}'), 404
        
        # Get all journal rows
        rows = FPJournalRowEU.query.filter_by(dataset_id=dataset.id).all()
        
        # Parse and combine data
        combined_data = []
        for row in rows:
            if row.row_json:
                try:
                    row_data = json.loads(row.row_json)
                    row_data['_journal_type'] = row.journal_type
                    row_data['_amount'] = row.amount
                    combined_data.append(row_data)
                except:
                    pass
        
        # Calculate summary
        total_count = len(combined_data)
        total_amount = sum(row.get('_amount', 0) for row in combined_data)
        
        # Get journal type breakdown
        type_breakdown = {}
        for row in rows:
            jtype = row.journal_type
            if jtype not in type_breakdown:
                type_breakdown[jtype] = {'count': 0, 'total': 0}
            type_breakdown[jtype]['count'] += 1
            type_breakdown[jtype]['total'] += (row.amount or 0)
        
        return render_template('view_combined_data_eu.html',
            job_id=job_id,
            data=combined_data,
            total_count=total_count,
            total_amount=total_amount,
            type_breakdown=type_breakdown)
        
    except Exception as e:
        return render_template('error.html', 
            message=f'Error loading data: {str(e)}',
            back_url=f'/journals-eu/?job_id={job_id}'), 500

@journals_eu_bp.route('/match-results/<int:job_id>')
def view_match_results(job_id):
    """View EU summit matching results"""
    try:
        FPDatasetEU = models['FPDatasetEU']
        FPMatchResultEU = models['FPMatchResultEU']
        
        dataset = FPDatasetEU.query.filter_by(job_id=job_id).first()
        if not dataset:
            return render_template('error.html',
                message='No EU dataset found',
                back_url=f'/journals-eu/?job_id={job_id}'), 404
        
        # Get all match results
        matched = FPMatchResultEU.query.filter_by(dataset_id=dataset.id, match_status='matched').all()
        insufficient = FPMatchResultEU.query.filter_by(dataset_id=dataset.id, match_status='insufficient').all()
        unmatched = FPMatchResultEU.query.filter_by(dataset_id=dataset.id, match_status='unmatched').all()
        
        # Calculate totals
        matched_total = sum(m.installment_amount for m in matched)
        insufficient_total = sum(m.installment_amount for m in insufficient)
        unmatched_total = sum(m.installment_amount for m in unmatched)
        
        return render_template('match_results_eu.html',
            job_id=job_id,
            subsidiary_id=4,  # EU is always subsidiary 4
            matched=matched,
            insufficient=insufficient,
            unmatched=unmatched,
            matched_total=matched_total,
            insufficient_total=insufficient_total,
            unmatched_total=unmatched_total,
            matched_count=len(matched),
            insufficient_count=len(insufficient),
            unmatched_count=len(unmatched))
        
    except Exception as e:
        return render_template('error.html',
            message=f'Error loading match results: {str(e)}',
            back_url=f'/journals-eu/?job_id={job_id}'), 500

@journals_eu_bp.route('/api/match-results/<int:job_id>/<int:subsidiary_id>')
def api_match_results(job_id, subsidiary_id):
    """API endpoint for EU match results data"""
    try:
        FPDatasetEU = models['FPDatasetEU']
        FPMatchResultEU = models['FPMatchResultEU']
        
        dataset = FPDatasetEU.query.filter_by(job_id=job_id).first()
        if not dataset:
            return jsonify({'success': False, 'error': 'No dataset found'}), 404
        
        # Get all match results
        matched = FPMatchResultEU.query.filter_by(dataset_id=dataset.id, match_status='matched').all()
        insufficient = FPMatchResultEU.query.filter_by(dataset_id=dataset.id, match_status='insufficient').all()
        unmatched = FPMatchResultEU.query.filter_by(dataset_id=dataset.id, match_status='unmatched').all()
        
        # Calculate totals for matched
        matched_total_received = sum(m.total_received or 0 for m in matched)
        matched_installment_total = sum(m.installment_amount for m in matched)
        matched_remaining_total = sum(m.remaining_amount or 0 for m in matched)
        
        # Calculate totals for insufficient and unmatched
        insufficient_total = sum(m.installment_amount for m in insufficient)
        unmatched_total = sum(m.installment_amount for m in unmatched)
        
        return jsonify({
            'success': True,
            'matched': [{
                'client_id': m.client_id,
                'total_received': m.total_received,
                'installment_amount': m.installment_amount,
                'remaining_amount': m.remaining_amount
            } for m in matched],
            'insufficient': [{
                'client_id': m.client_id,
                'total_received': m.total_received,
                'installment_amount': m.installment_amount,
                'remaining_amount': m.remaining_amount
            } for m in insufficient],
            'unmatched': [{
                'client_id': m.client_id,
                'installment_amount': m.installment_amount
            } for m in unmatched],
            'totals': {
                'matched_count': len(matched),
                'matched_total_received': matched_total_received,
                'matched_installment': matched_installment_total,
                'matched_remaining': matched_remaining_total,
                'insufficient_count': len(insufficient),
                'insufficient_total': insufficient_total,
                'unmatched_count': len(unmatched),
                'unmatched_total': unmatched_total
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== CROSS-SUBSIDIARY SPLITTER ====================

@journals_eu_bp.route('/api/split-cross-sub/<int:job_id>', methods=['POST'])
def split_cross_subsidiary(job_id):
    """Split Cross-Subsidiary CSV into Main, POA, and Refunds"""
    import pandas as pd
    import os
    from datetime import datetime
    import traceback
    
    try:
        print(f"[DEBUG] Split Cross-Sub called for job_id={job_id}")
        if 'file' not in request.files:
            print("[DEBUG] No file in request")
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        print(f"[DEBUG] File received: {file.filename}")
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Only CSV files are supported'}), 400
        
        # Read CSV with proper encoding handling
        print("[DEBUG] Reading CSV...")
        df = pd.read_csv(file, encoding='cp1252')  # Windows-1252 encoding for NetSuite compatibility
        print(f"[DEBUG] CSV read successfully, shape: {df.shape}")
        
        # Split logic:
        # - Refunds: amount < 0
        # - POA: invoice_number contains "POA" (case insensitive)
        # - Main: everything else
        
        refunds = df[df['amount'].astype(float) < 0].copy()
        poa = df[(df['amount'].astype(float) >= 0) & (df['invoice_number'].astype(str).str.contains('POA', case=False, na=False))].copy()
        main = df[(df['amount'].astype(float) >= 0) & (~df['invoice_number'].astype(str).str.contains('POA', case=False, na=False))].copy()
        
        # Save to temp directory
        output_dir = f"generated_journals/cross_sub_splits/job_{job_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        main_path = os.path.join(output_dir, f"Cross_Subsidiary_Main_{timestamp}.csv")
        poa_path = os.path.join(output_dir, f"Cross_Subsidiary_POA_{timestamp}.csv")
        refunds_path = os.path.join(output_dir, f"Cross_Subsidiary_Refunds_{timestamp}.csv")
        
        # Write with Windows-1252 encoding for NetSuite compatibility
        main.to_csv(main_path, index=False, encoding='cp1252')
        poa.to_csv(poa_path, index=False, encoding='cp1252')
        refunds.to_csv(refunds_path, index=False, encoding='cp1252')
        
        return jsonify({
            'success': True,
            'files': [
                {'type': 'Main', 'count': len(main), 'path': main_path},
                {'type': 'POA', 'count': len(poa), 'path': poa_path},
                {'type': 'Refunds', 'count': len(refunds), 'path': refunds_path}
            ]
        })
        
    except Exception as e:
        print(f"[ERROR] Split Cross-Sub failed: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@journals_eu_bp.route('/api/download-cross-sub-split/<int:job_id>/<split_type>')
def download_cross_sub_split(job_id, split_type):
    """Download a specific split file"""
    import glob
    import os
    from flask import send_file
    
    try:
        output_dir = f"generated_journals/cross_sub_splits/job_{job_id}"
        pattern = os.path.join(output_dir, f"Cross_Subsidiary_{split_type}_*.csv")
        files = glob.glob(pattern)
        
        if not files:
            return jsonify({'success': False, 'error': f'No {split_type} file found'}), 404
        
        # Get the most recent file
        latest_file = max(files, key=os.path.getctime)
        
        return send_file(latest_file, as_attachment=True, download_name=os.path.basename(latest_file))
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@journals_eu_bp.route('/api/download-cross-sub-splits-zip/<int:job_id>')
def download_cross_sub_splits_zip(job_id):
    """Download all split files as ZIP"""
    import glob
    import os
    import zipfile
    import io
    from flask import send_file
    from datetime import datetime
    
    try:
        output_dir = f"generated_journals/cross_sub_splits/job_{job_id}"
        
        # Find all CSV files in the directory
        csv_files = glob.glob(os.path.join(output_dir, "*.csv"))
        
        if not csv_files:
            return jsonify({'success': False, 'error': 'No split files found'}), 404
        
        # Create ZIP in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for csv_file in csv_files:
                zf.write(csv_file, os.path.basename(csv_file))
        
        memory_file.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'Cross_Subsidiary_Splits_{timestamp}.zip'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
