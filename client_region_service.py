"""Build and query client → Stripe region mapping from MatchedTransaction data."""

import json
from collections import defaultdict
from datetime import datetime

SUBSIDIARY_LABELS = {
    1: 'AU',
    2: 'CA',
    3: 'US',
    4: 'EU',
    5: 'UK',
}


def _is_summit_match(match_type):
    if not match_type:
        return False
    return 'summit' in str(match_type).lower()


def rebuild_client_regions(db, MatchedTransaction, ClientRegionHistory, ClientRegionProfile):
    """Rebuild history + profile tables from matched_transactions."""
    matches = MatchedTransaction.query.filter(
        MatchedTransaction.cb_client_id.isnot(None)
    ).all()

    skipped_summit = 0
    history_buckets = {}

    for m in matches:
        if _is_summit_match(m.match_type):
            skipped_summit += 1
            continue
        client_id = str(m.cb_client_id).strip()
        if not client_id:
            continue
        key = (client_id, m.subsidiary_id, m.job_id)
        if key not in history_buckets:
            history_buckets[key] = {
                'match_count': 0,
                'stripe_total': 0.0,
                'billing_counts': defaultdict(int),
                'match_types': defaultdict(int),
            }
        bucket = history_buckets[key]
        bucket['match_count'] += 1
        bucket['stripe_total'] += float(m.stripe_amount or 0)
        if m.cb_billing_entity:
            bucket['billing_counts'][m.cb_billing_entity] += 1
        mt = m.match_type or 'unknown'
        bucket['match_types'][mt] += 1

    ClientRegionHistory.query.delete()
    ClientRegionProfile.query.delete()
    db.session.flush()

    profile_data = defaultdict(lambda: {
        'region_counts': defaultdict(int),
        'regions': set(),
        'total_matches': 0,
        'last_job_id': 0,
        'last_subsidiary_id': None,
        'last_billing_entity': None,
    })

    for (client_id, subsidiary_id, job_id), bucket in history_buckets.items():
        billing_entity = None
        if bucket['billing_counts']:
            billing_entity = max(bucket['billing_counts'].items(), key=lambda x: x[1])[0]

        hist = ClientRegionHistory(
            client_id=client_id,
            subsidiary_id=subsidiary_id,
            job_id=job_id,
            match_count=bucket['match_count'],
            billing_entity=billing_entity,
            match_types_json=json.dumps(dict(bucket['match_types'])),
            total_stripe_amount=round(bucket['stripe_total'], 2),
            updated_at=datetime.utcnow(),
        )
        db.session.add(hist)

        p = profile_data[client_id]
        p['region_counts'][subsidiary_id] += bucket['match_count']
        p['regions'].add(subsidiary_id)
        p['total_matches'] += bucket['match_count']
        if job_id >= p['last_job_id']:
            p['last_job_id'] = job_id
            p['last_subsidiary_id'] = subsidiary_id
            p['last_billing_entity'] = billing_entity

    multi_region_count = 0
    for client_id, p in profile_data.items():
        region_counts = dict(p['region_counts'])
        regions = sorted(p['regions'])
        is_multi = len(regions) > 1
        if is_multi:
            multi_region_count += 1

        primary_sub = None
        if region_counts:
            max_count = max(region_counts.values())
            candidates = [sid for sid, cnt in region_counts.items() if cnt == max_count]
            primary_sub = min(candidates)

        profile = ClientRegionProfile(
            client_id=client_id,
            primary_subsidiary_id=primary_sub,
            is_multi_region=is_multi,
            regions_json=json.dumps(regions),
            region_counts_json=json.dumps({str(k): v for k, v in region_counts.items()}),
            last_subsidiary_id=p['last_subsidiary_id'],
            last_job_id=p['last_job_id'],
            last_billing_entity=p['last_billing_entity'],
            total_matches=p['total_matches'],
            updated_at=datetime.utcnow(),
        )
        db.session.add(profile)

    db.session.commit()

    return {
        'clients': len(profile_data),
        'history_rows': len(history_buckets),
        'multi_region_clients': multi_region_count,
        'skipped_summit_matches': skipped_summit,
        'source_matches': len(matches),
    }


def profile_to_api_dict(profile, job_names=None):
    """Serialize profile for API responses."""
    job_names = job_names or {}
    regions = json.loads(profile.regions_json or '[]')
    region_counts = json.loads(profile.region_counts_json or '{}')
    return {
        'client_id': profile.client_id,
        'primary_subsidiary_id': profile.primary_subsidiary_id,
        'primary_region': SUBSIDIARY_LABELS.get(profile.primary_subsidiary_id, '?'),
        'is_multi_region': profile.is_multi_region,
        'regions': [SUBSIDIARY_LABELS.get(r, str(r)) for r in regions],
        'region_ids': regions,
        'region_counts': {SUBSIDIARY_LABELS.get(int(k), k): v for k, v in region_counts.items()},
        'last_subsidiary_id': profile.last_subsidiary_id,
        'last_region': SUBSIDIARY_LABELS.get(profile.last_subsidiary_id, '?'),
        'last_job_id': profile.last_job_id,
        'last_job_name': job_names.get(profile.last_job_id, f'Job {profile.last_job_id}'),
        'last_billing_entity': profile.last_billing_entity,
        'total_matches': profile.total_matches,
        'updated_at': profile.updated_at.isoformat() if profile.updated_at else None,
    }
