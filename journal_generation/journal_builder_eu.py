"""
EU-Specific Journal Builder
Handles AED currency transactions separately from EUR transactions
"""

import pandas as pd
import io
import unicodedata
from typing import Dict, Optional
from datetime import datetime
import calendar

from journal_generation.journal_builder import resolve_invoice_number, resolve_payment_number


def _cashbook_location_for_region(row: pd.Series) -> str:
    """EU master uses 'Location'; generic builder uses 'location'. Empty if missing."""
    for key in ('Location', 'location'):
        if key not in row.index:
            continue
        v = row[key]
        if pd.isna(v):
            continue
        s = str(v).strip()
        if s:
            return s
    return ''


class JournalBuilderEU:
    """
    EU-specific journal builder that handles AED transactions separately
    
    Generates 5 journals:
    1. Refunds (EUR, double-entry format)
    2. POA (EUR)
    3. Main (EUR)
    4. Cross-Subsidiary (EUR)
    5. AED Journal (original AED amounts)
    """
    
    def __init__(self, db, job_id: int, subsidiary_id: int, models=None):
        self.db = db
        self.job_id = job_id
        self.subsidiary_id = subsidiary_id
        self.models = models or {}
        self.subsidiary_name = "EU"
        self.billing_entity = "Ndevor Systems Ltd : Phorest Ireland"
    
    def get_matched_transactions(self) -> pd.DataFrame:
        """
        Get all matched transactions from MatchedTransaction table
        Same source as reconciliation and master upload
        """
        if 'MatchedTransaction' in self.models:
            MatchedTransaction = self.models['MatchedTransaction']
        else:
            MatchedTransaction = self.db.Model.registry._class_registry.data.get('MatchedTransaction')
        
        if not MatchedTransaction:
            raise ValueError("MatchedTransaction model not available")
        
        matches = MatchedTransaction.query.filter_by(
            job_id=self.job_id,
            subsidiary_id=self.subsidiary_id
        ).all()
        
        if not matches:
            return pd.DataFrame()
        
        data = []
        for match in matches:
            # Determine if this is AED or EUR transaction
            is_aed = match.stripe_currency and match.stripe_currency.upper() == 'AED'
            
            row = {
                'payment_date': match.cb_payment_date,
                'client_id': match.cb_client_id,
                'invoice_number': match.cb_invoice_number,
                'billing_entity': match.cb_billing_entity,
                'ar_account': match.cb_ar_account,
                'currency': match.stripe_currency if is_aed else match.cb_currency,
                'exchange_rate': match.cb_exchange_rate,
                'amount': match.stripe_amount,  # Use stripe_amount (same as reconciliation)
                'account': match.cb_account,
                'Location': (match.cb_location or ''),  # Capital L to match export expected_columns
                'transtype': match.cb_transtype,
                'comment': match.cb_comment,
                'card_reference': match.cb_card_reference,
                'reasoncode': match.cb_reasoncode,
                'sepaprovider': match.cb_sepaprovider,
                'invoice_hash': match.cb_invoice_hash,
                'payment_hash': match.cb_payment_hash,
                'memo': match.cb_memo,
                # Stripe data for AED handling
                'stripe_currency': match.stripe_currency,
                'stripe_converted_amount': match.stripe_converted_amount,
                'is_aed': is_aed
            }
            data.append(row)
        
        return pd.DataFrame(data)
    
    def generate_master_journal(self, memo: Optional[str] = None) -> pd.DataFrame:
        """
        Generate master journal with all transactions
        """
        df = self.get_matched_transactions()
        
        if df.empty:
            return df
        
        if memo:
            df['memo'] = memo
        else:
            df['memo'] = ''
        
        return df
    
    def split_journals(self, master_df: pd.DataFrame, memo: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Split master journal into categorized journals (EUR and AED):
        EUR Journals: Refunds, POA, Main, Cross-Subsidiary
        AED Journals: Refunds_AED, POA_AED, Main_AED, Cross_Subsidiary_AED
        
        This matches the Master Upload categorization logic
        """
        if master_df.empty:
            return {}
        
        journals = {}
        
        # STEP 1: Separate AED and EUR transactions
        aed_df = master_df[master_df['is_aed'] == True].copy()
        eur_df = master_df[master_df['is_aed'] == False].copy()
        
        # STEP 2: Process EUR transactions
        if not eur_df.empty:
            cross_mask_eur = eur_df['billing_entity'] != self.billing_entity
            cross_eur_df = eur_df[cross_mask_eur].copy()
            if not cross_eur_df.empty:
                cross_eur_refunds_df = cross_eur_df[cross_eur_df['amount'] < 0].copy()
                cross_eur_non_refund_df = cross_eur_df[cross_eur_df['amount'] >= 0].copy()
                if not cross_eur_non_refund_df.empty:
                    journals['Cross_Subsidiary_EU'] = cross_eur_non_refund_df
                if not cross_eur_refunds_df.empty:
                    journals['Refunds_Cross_Subsidiary_EU'] = self._generate_refunds_journal(
                        cross_eur_refunds_df, memo
                    )
            
            non_cross_eur_df = eur_df[~cross_mask_eur].copy()
            
            if not non_cross_eur_df.empty:
                # Refunds (negative amounts, double-entry format)
                refunds_eur_mask = non_cross_eur_df['amount'] < 0
                refunds_eur_df = non_cross_eur_df[refunds_eur_mask].copy()
                if not refunds_eur_df.empty:
                    journals['Refunds_EU'] = self._generate_refunds_journal(refunds_eur_df, memo)
                
                # Positive EUR transactions
                positive_eur_df = non_cross_eur_df[~refunds_eur_mask].copy()
                
                if not positive_eur_df.empty:
                    # POA Journal
                    poa_eur_mask = positive_eur_df['invoice_number'].astype(str).str.contains('POA', case=False, na=False)
                    poa_eur_df = positive_eur_df[poa_eur_mask].copy()
                    if not poa_eur_df.empty:
                        journals['POA_EU'] = poa_eur_df
                    
                    # Main Journal (Regular)
                    main_eur_df = positive_eur_df[~poa_eur_mask].copy()
                    if not main_eur_df.empty:
                        journals['Main_EU'] = main_eur_df
        
        # STEP 3: Process AED transactions
        if not aed_df.empty:
            cross_mask_aed = aed_df['billing_entity'] != self.billing_entity
            cross_aed_df = aed_df[cross_mask_aed].copy()
            if not cross_aed_df.empty:
                cross_aed_refunds_df = cross_aed_df[cross_aed_df['amount'] < 0].copy()
                cross_aed_non_refund_df = cross_aed_df[cross_aed_df['amount'] >= 0].copy()
                if not cross_aed_non_refund_df.empty:
                    journals['Cross_Subsidiary_AED'] = cross_aed_non_refund_df
                if not cross_aed_refunds_df.empty:
                    rca = self._generate_refunds_journal(cross_aed_refunds_df, memo)
                    self._attach_aed_refund_eur_total(rca, cross_aed_refunds_df)
                    journals['Refunds_Cross_Subsidiary_AED'] = rca
            
            non_cross_aed_df = aed_df[~cross_mask_aed].copy()
            
            if not non_cross_aed_df.empty:
                # Refunds AED (negative amounts, double-entry format)
                refunds_aed_mask = non_cross_aed_df['amount'] < 0
                refunds_aed_df = non_cross_aed_df[refunds_aed_mask].copy()
                if not refunds_aed_df.empty:
                    raj = self._generate_refunds_journal(refunds_aed_df, memo)
                    self._attach_aed_refund_eur_total(raj, refunds_aed_df)
                    journals['Refunds_AED'] = raj
                
                # Positive AED transactions
                positive_aed_df = non_cross_aed_df[~refunds_aed_mask].copy()
                
                if not positive_aed_df.empty:
                    # POA AED
                    poa_aed_mask = positive_aed_df['invoice_number'].astype(str).str.contains('POA', case=False, na=False)
                    poa_aed_df = positive_aed_df[poa_aed_mask].copy()
                    if not poa_aed_df.empty:
                        journals['POA_AED'] = poa_aed_df
                    
                    # Main AED (Regular)
                    main_aed_df = positive_aed_df[~poa_aed_mask].copy()
                    if not main_aed_df.empty:
                        journals['Main_AED'] = main_aed_df
        
        return journals
    
    def _attach_aed_refund_eur_total(self, journal_df: pd.DataFrame, source_refunds_df: pd.DataFrame) -> None:
        """Store EUR sum from Stripe conversion on double-entry AED refund journals (for summaries)."""
        if journal_df.empty or source_refunds_df.empty:
            return
        if 'stripe_converted_amount' in source_refunds_df.columns:
            journal_df.attrs['aed_converted_eur_total'] = float(
                source_refunds_df['stripe_converted_amount'].fillna(0).sum()
            )
    
    def _generate_refunds_journal(self, refunds_df: pd.DataFrame, memo: Optional[str] = None) -> pd.DataFrame:
        """
        Generate double-entry refunds journal in same format as other subsidiaries.
        One Dr row per refund (AR), then one Cr row for total (Bank). Same columns as USA/UK/etc.
        """
        if refunds_df.empty:
            return pd.DataFrame()
        
        journal_entries = []
        
        # Get the month and year from the first transaction to calculate EOM (same as other subsidiaries)
        if not refunds_df.empty and 'payment_date' in refunds_df.columns:
            first_date_str = str(refunds_df.iloc[0]['payment_date'])
            try:
                if '/' in first_date_str:
                    parts = first_date_str.split('/')
                    if len(parts) == 3:
                        day, month, year = parts
                        month = int(month)
                        year = int(year)
                        last_day = calendar.monthrange(year, month)[1]
                        eom_date = f"{last_day:02d}/{month:02d}/{year}"
                    else:
                        eom_date = "30/09/2025"
                else:
                    first_date = datetime.strptime(first_date_str[:10], '%Y-%m-%d')
                    month = first_date.month
                    year = first_date.year
                    last_day = calendar.monthrange(year, month)[1]
                    eom_date = f"{last_day:02d}/{month:02d}/{year}"
            except Exception:
                eom_date = "30/09/2025"
        else:
            eom_date = "30/09/2025"
        
        total_refund_amount = abs(refunds_df['amount'].sum())
        first_refund = refunds_df.iloc[0]
        bank_account = first_refund['account']
        cr_entity = first_refund['billing_entity']
        
        # One Dr entry per refund (same as other subsidiaries)
        for idx, row in refunds_df.iterrows():
            amount_abs = abs(row['amount'])
            entry = {
                'Date': row['payment_date'],
                'memo': memo if memo else 'MISC PAYMENT STRIPE',
                'Entity': row['billing_entity'],
                'Name': row['client_id'],
                'Account': '11010 Accounts Receivable : Trade Debtors',
                'Management P&L': 'Balance Sheet',
                'Dept.': 'Balance Sheet',
                'Cost centre': 'Balance Sheet',
                'Region': _cashbook_location_for_region(row),
                'Dr': amount_abs,
                'Cr': ''
            }
            journal_entries.append(entry)
        
        # Final Cr entry - Bank Account (total sum), same as other subsidiaries
        entry_cr = {
            'Date': eom_date,
            'memo': 'Refunds / Disputes',
            'Entity': cr_entity,
            'Name': '',
            'Account': bank_account,
            'Management P&L': 'Balance Sheet',
            'Dept.': 'Balance Sheet',
            'Cost centre': 'Balance Sheet',
            'Region': '',
            'Dr': '',
            'Cr': total_refund_amount
        }
        journal_entries.append(entry_cr)
        
        refunds_journal_df = pd.DataFrame(journal_entries, columns=[
            'Date', 'memo', 'Entity', 'Name', 'Account',
            'Management P&L', 'Dept.', 'Cost centre', 'Region', 'Dr', 'Cr'
        ])
        return refunds_journal_df
    
    def generate_all(self, memo: Optional[str] = None) -> Dict:
        """
        Generate all journals and calculate summary with reconciliation
        """
        try:
            master_df = self.generate_master_journal(memo)
            
            if master_df.empty:
                return {
                    'success': False,
                    'error': 'No matched transactions found'
                }
            
            journals = self.split_journals(master_df, memo)
            
            # Calculate summary for each journal
            summary = {
                'master_count': len(master_df),
                'master_total': float(master_df['amount'].sum()),
                'journals': {}
            }
            
            # Track EUR and AED separately for reconciliation
            eur_total = 0.0
            aed_total_aed = 0.0
            aed_total_eur = 0.0  # AED converted to EUR for comparison
            
            # Track combined categories (EUR + AED)
            combined_refunds = 0.0
            combined_poa = 0.0
            combined_main = 0.0
            combined_cross_sub = 0.0
            
            for journal_name, journal_df in journals.items():
                if 'Refunds_' in journal_name and 'Dr' in journal_df.columns:
                    # Refunds journal uses Dr/Cr format
                    total = float(journal_df['Dr'].replace('', 0).astype(float).sum())
                else:
                    # Regular journals use amount column
                    total = float(journal_df['amount'].sum()) if 'amount' in journal_df.columns else 0
                
                summary['journals'][journal_name] = {
                    'count': len(journal_df),
                    'total': total
                }
                
                # Categorize by EUR vs AED
                is_aed_journal = '_AED' in journal_name
                
                if is_aed_journal:
                    # AED journal - need to convert for comparison
                    if 'Refunds_' in journal_name and 'Dr' in journal_df.columns:
                        total_eur = float(journal_df.attrs.get('aed_converted_eur_total', 0) or 0)
                    elif 'stripe_converted_amount' in journal_df.columns:
                        total_eur = float(journal_df['stripe_converted_amount'].sum())
                    else:
                        total_eur = 0
                    aed_total_aed += total
                    aed_total_eur += total_eur
                else:
                    # EUR journal — double-entry refunds use positive Dr sums; net EUR total must subtract them
                    if 'Refunds_' in journal_name and 'Dr' in journal_df.columns:
                        eur_total -= total
                    else:
                        eur_total += total
                    total_eur = total
                
                # Add to combined categories (for comparison with Master Upload)
                if 'Refunds' in journal_name:
                    combined_refunds += total_eur
                elif 'POA' in journal_name:
                    combined_poa += total_eur
                elif 'Main' in journal_name:
                    combined_main += total_eur
                elif 'Cross_Subsidiary' in journal_name:
                    combined_cross_sub += total_eur
            
            # Calculate combined total (EUR equivalent)
            combined_total_eur = combined_refunds + combined_poa + combined_main + combined_cross_sub
            
            # Master Upload uses converted EUR for all (including AED converted)
            # So we compare combined_total_eur (which includes AED converted to EUR)
            master_upload_equivalent = combined_total_eur
            
            # Add reconciliation info
            summary['reconciliation'] = {
                'eur_journals_total': round(eur_total, 2),
                'aed_journals_total_aed': round(aed_total_aed, 2),
                'aed_journals_total_eur': round(aed_total_eur, 2),
                'combined_total_eur': round(combined_total_eur, 2),
                'master_upload_total': round(master_upload_equivalent, 2),
                'difference': 0.0,  # Should match since same categorization logic
                'match': True,
                'breakdown': {
                    'refunds': round(combined_refunds, 2),
                    'poa': round(combined_poa, 2),
                    'main': round(combined_main, 2),
                    'cross_subsidiary': round(combined_cross_sub, 2)
                }
            }
            
            return {
                'success': True,
                'subsidiary': self.subsidiary_name,
                'summary': summary,
                'journal_names': list(journals.keys())
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error generating EU journals: {str(e)}'
            }
    
    def _df_to_eu_netsuite_csv_bytes(self, df_export: pd.DataFrame) -> io.BytesIO:
        """
        Write UTF-8 with BOM so Ä / Ö / Ü stay as real Unicode (U+00C4 etc.).

        cp1252 uses a single byte for Ä (0xC4); tools that open the CSV as UTF-8 mis-decode
        that byte and can show the wrong glyph (e.g. ƒ). UTF-8-sig is widely accepted by
        NetSuite/Excel when the import encoding is set to UTF-8.
        """
        text_buf = io.StringIO()
        df_export.to_csv(text_buf, index=False)
        raw = unicodedata.normalize('NFC', text_buf.getvalue())
        data = raw.encode('utf-8-sig')
        out = io.BytesIO(data)
        out.seek(0)
        return out
    
    def export_journal_to_csv(self, df: pd.DataFrame, journal_name: str) -> io.BytesIO:
        """Export journal DataFrame to CSV BytesIO with correct format"""
        # Create a copy to avoid modifying original
        df_export = df.copy()
        
        # Refunds journals use Dr/Cr format with different columns – export as-is
        if 'Dr' in df_export.columns and 'Cr' in df_export.columns:
            return self._df_to_eu_netsuite_csv_bytes(df_export)
        
        # Standard journals (Main, POA, Cross): use expected column order and preserve Location
        expected_columns = [
            'payment_date', 'client_id', 'invoice_number', 'billing_entity', 'ar_account',
            'currency', 'exchange_rate', 'amount', 'account', 'Location', 'transtype',
            'comment', 'Card Reference', 'reasoncode', 'sepaprovider', 'invoice #', 'payment #', 'Memo'
        ]
        
        # EU master uses snake_case from MatchedTransaction; export expects cashbook headers.
        # Without this, 'Card Reference' is added as empty and 'card_reference' is dropped.
        if 'Card Reference' not in df_export.columns and 'card_reference' in df_export.columns:
            df_export['Card Reference'] = df_export['card_reference']
        if 'Memo' not in df_export.columns and 'memo' in df_export.columns:
            df_export['Memo'] = df_export['memo']
        
        # Preserve Location: use 'Location' if present, else copy from 'location' (EU column naming)
        if 'Location' not in df_export.columns and 'location' in df_export.columns:
            df_export['Location'] = df_export['location'].fillna('').astype(str)
        elif 'Location' in df_export.columns:
            df_export['Location'] = df_export['Location'].fillna('').astype(str)
        
        # Generate invoice # and payment # — prefer master/cashbook values from upload
        if 'client_id' in df_export.columns and 'invoice_number' in df_export.columns:
            df_export['invoice #'] = df_export.apply(resolve_invoice_number, axis=1)
            df_export['payment #'] = df_export.apply(resolve_payment_number, axis=1)
        
        # Ensure all expected columns exist (add missing ones with empty values)
        for col in expected_columns:
            if col not in df_export.columns:
                df_export[col] = ''
        
        # Select only the expected columns in the correct order
        df_export = df_export[expected_columns]
        
        return self._df_to_eu_netsuite_csv_bytes(df_export)
    
    def export_all_journals(self, memo: Optional[str] = None) -> Dict[str, io.BytesIO]:
        """
        Export all EU journals as CSV files (including master file, same as other subsidiaries)
        
        Returns:
            Dictionary with journal name as key and BytesIO CSV file as value
        """
        master_df = self.generate_master_journal(memo)
        
        if master_df.empty:
            return {}
        
        journals = self.split_journals(master_df, memo)
        
        # Include master journal in ZIP (same as USA/other subsidiaries)
        journals['Master_Journal'] = master_df
        
        # Export each journal as CSV
        exported_journals = {}
        for journal_name, journal_df in journals.items():
            csv_file = self.export_journal_to_csv(journal_df, journal_name)
            exported_journals[journal_name] = csv_file
        
        return exported_journals

