#!/usr/bin/env python3
"""
One-off script to check EU refund discrepancy in DB (Jan 26).
Run from project root: python scripts/check_eu_refunds_db.py

Finds EU job(s) (subsidiary_id=4) and reports:
- Master file refund total = sum(cb_amount) where cb_amount < 0 (all matched rows)
- Complete Reconciliation Summary refund total = sum(stripe amount) where amount < 0
  from matched rows EXCLUDING match_type 'Salon Summit Installment'
- Breakdown by match_type for refund rows.
"""

import os
import sys

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    from app import app
    from models import create_models
    from app import db

    with app.app_context():
        # Resolve model classes
        from app import MatchedTransaction

        # EU = subsidiary_id 4
        subsidiary_id = 4

        # All jobs that have EU (subsidiary 4) matched transactions
        job_ids = db.session.query(MatchedTransaction.job_id).filter_by(
            subsidiary_id=subsidiary_id
        ).distinct().all()
        job_ids = [r[0] for r in job_ids]

        if not job_ids:
            print("No matched transactions found for EU (subsidiary_id=4).")
            return

        from app import ProcessingJob
        jobs_info = {}
        for jid in job_ids:
            job = ProcessingJob.query.get(jid)
            jobs_info[jid] = job.job_name if job else f"Job {jid}"

        print("=" * 60)
        print("EU (subsidiary_id=4) – Refund discrepancy check")
        print("=" * 60)

        for job_id in sorted(job_ids):
            job_name = jobs_info.get(job_id, f"Job {job_id}")
            print(f"\n--- Job ID: {job_id}  Name: {job_name} ---\n")

            # ALL matched (what master file uses)
            all_matches = MatchedTransaction.query.filter_by(
                job_id=job_id,
                subsidiary_id=subsidiary_id
            ).all()

            # Matches EXCLUDING Salon Summit Installment (what Complete Reconciliation Summary uses)
            summary_matches = MatchedTransaction.query.filter_by(
                job_id=job_id,
                subsidiary_id=subsidiary_id
            ).filter(MatchedTransaction.match_type != 'Salon Summit Installment').all()

            total_matched = len(all_matches)
            summary_matched = len(summary_matches)
            ssi_count = total_matched - summary_matched

            print(f"Matched rows: total = {total_matched}, excluding Salon Summit Installment = {summary_matched}, Salon Summit Installment = {ssi_count}")

            # Master file: uses cb_amount from ALL matches (Cashbook format)
            cb_refund_sum = 0.0
            cb_refund_count = 0
            for m in all_matches:
                if m.cb_amount is not None and m.cb_amount < 0:
                    cb_refund_sum += m.cb_amount
                    cb_refund_count += 1

            print(f"\n1) MASTER FILE (All Matched Transactions) – uses Cashbook amount (cb_amount):")
            print(f"   Refund rows (cb_amount < 0): count = {cb_refund_count}, sum(cb_amount) = {cb_refund_sum:.2f}")
            print(f"   (Absolute value of refunds in file: {abs(cb_refund_sum):.2f})")

            # Complete Reconciliation Summary: uses stripe amount (or stripe_converted_amount for AED) from summary_matches only
            refund_sum_stripe = 0.0
            refund_count_stripe = 0
            for m in summary_matches:
                if subsidiary_id == 4 and m.stripe_currency and str(m.stripe_currency).upper() == 'AED':
                    amt = m.stripe_converted_amount or m.stripe_amount or 0
                else:
                    amt = m.stripe_amount or 0
                if amt < 0:
                    refund_sum_stripe += amt
                    refund_count_stripe += 1

            print(f"\n2) COMPLETE RECONCILIATION SUMMARY – uses Stripe amount (excl. Salon Summit Installment):")
            print(f"   Refund rows (amount < 0): count = {refund_count_stripe}, sum = {refund_sum_stripe:.2f}")

            # Same stripe-based refund total but over ALL matches (to see impact of SSI exclusion)
            refund_sum_stripe_all = 0.0
            refund_count_stripe_all = 0
            for m in all_matches:
                if subsidiary_id == 4 and m.stripe_currency and str(m.stripe_currency).upper() == 'AED':
                    amt = m.stripe_converted_amount or m.stripe_amount or 0
                else:
                    amt = m.stripe_amount or 0
                if amt < 0:
                    refund_sum_stripe_all += amt
                    refund_count_stripe_all += 1

            print(f"\n3) If Summary included Salon Summit Installment (Stripe amount):")
            print(f"   Refund rows: count = {refund_count_stripe_all}, sum = {refund_sum_stripe_all:.2f}")

            # Breakdown of refund rows (cb_amount < 0) by match_type
            from collections import defaultdict
            refund_by_type = defaultdict(lambda: {'count': 0, 'cb_sum': 0.0, 'stripe_sum': 0.0})
            for m in all_matches:
                if m.cb_amount is not None and m.cb_amount < 0:
                    t = m.match_type or 'NULL'
                    refund_by_type[t]['count'] += 1
                    refund_by_type[t]['cb_sum'] += m.cb_amount
                    if subsidiary_id == 4 and m.stripe_currency and str(m.stripe_currency).upper() == 'AED':
                        amt = m.stripe_converted_amount or m.stripe_amount or 0
                    else:
                        amt = m.stripe_amount or 0
                    refund_by_type[t]['stripe_sum'] += amt if amt < 0 else 0

            print(f"\n4) Refund rows (cb_amount < 0) by match_type:")
            for match_type, d in sorted(refund_by_type.items(), key=lambda x: -abs(x[1]['cb_sum'])):
                print(f"   {match_type!r}: count={d['count']}, sum(cb_amount)={d['cb_sum']:.2f}, sum(stripe_amount)={d['stripe_sum']:.2f}")

            # Difference: Cashbook vs Stripe for same set (summary_matches only)
            cb_refund_sum_summary_only = 0.0
            for m in summary_matches:
                if m.cb_amount is not None and m.cb_amount < 0:
                    cb_refund_sum_summary_only += m.cb_amount
            print(f"\n5) For same set (excl. Salon Summit Installment):")
            print(f"   sum(cb_amount) where cb_amount < 0 = {cb_refund_sum_summary_only:.2f}")
            print(f"   sum(stripe amount) where amount < 0 = {refund_sum_stripe:.2f}")
            print(f"   Difference (Cashbook - Stripe) = {cb_refund_sum_summary_only - refund_sum_stripe:.2f}")

        print("\n" + "=" * 60)

        # For Jan 26 (Job 8): also report raw Stripe file totals (charge + refund only, like summary)
        if 8 in job_ids:
            from app import StripeTransaction
            stripe_all = StripeTransaction.query.filter_by(job_id=8, subsidiary_id=4).all()
            stripe_refund_only = 0.0
            stripe_refund_only_count = 0
            for tx in stripe_all:
                ty = (tx.type or '').lower()
                if ty not in ('charge', 'refund'):
                    continue
                amt = tx.amount or 0
                if amt < 0:
                    stripe_refund_only_count += 1
                    if tx.currency and str(tx.currency).upper() == 'AED':
                        stripe_refund_only += tx.converted_amount or tx.amount or 0
                    else:
                        stripe_refund_only += tx.amount or 0
            print("\n--- Job 8 (Jan 26) – Stripe file (charge/refund only, amount<0) ---")
            print(f"   Refund rows in stripe_transactions: count={stripe_refund_only_count}, sum={stripe_refund_only:.2f}")

if __name__ == '__main__':
    main()
