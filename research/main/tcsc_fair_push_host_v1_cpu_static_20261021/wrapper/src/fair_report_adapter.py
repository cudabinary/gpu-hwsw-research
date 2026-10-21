"""Validate saved real CPU-owner reports without inventing GPU event metrics."""
import hashlib, json

def parse_cpu_owner(stdout, distances, expected_sha256, n, q, mode):
    row = json.loads(stdout)
    if row['status'] != 'CPU_ONLY_PASS' or row['driver_loaded'] or row['GPU_launches']:
        raise ValueError('NOT_A_CPU_OWNER_REPORT')
    if (row['arrays'], row['mode']) != (q, mode) or len(distances) != 4*n*q:
        raise ValueError('OWNER_RESULT_SHAPE')
    if hashlib.sha256(distances).hexdigest() != expected_sha256:
        raise ValueError('OWNER_DISTANCE_HASH')
    if mode not in [5, 7] or row['reverse_present'] != (mode == 5):
        raise ValueError('FAIR_PREPARATION_MODE')
    if mode == 7 and (row['cpu_reverse_build_ms'] != 0 or row['metadata_bytes'] != 8*((n+63)//64)):
        raise ValueError('PUSH_PREPARATION_CHARGING')
    if row['preparation_peak_bytes'] > 32 << 20 or row['projected_device_payload_bytes'] > 32 << 20:
        raise ValueError('COMMON_CAP_EXCEEDED')
    return {'kind': 'REAL_COMPILED_CPU_OWNER_NOT_GPU', 'mode': mode, 'q': q,
            'metrics': {k: row[k] for k in ['algorithm_preparation_ms', 'cpu_reverse_build_ms', 'cpu_static_bound_ms']},
            'CPU_preparation_account_live_bytes': row['preparation_payload_bytes'],
            'CPU_preparation_account_peak_bytes': row['preparation_peak_bytes'],
            'projected_device_bytes_NOT_MEASURED': row['projected_device_payload_bytes'],
            'GPU_event_ms': 'UNKNOWN_NOT_EXECUTED', 'native_alloc_and_H2D_ms': 'UNKNOWN_NOT_EXECUTED',
            'GPU_driver_physical_peak': 'UNKNOWN', 'CPU_output_hash': expected_sha256}
