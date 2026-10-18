import argparse
import fcntl
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'controllers/runtime'))
sys.path.insert(0, str(ROOT / 'controllers/orchestration'))
from common import ensure_hash_seed, load_config, sha256


def main():
    parser = argparse.ArgumentParser(description='Replay an archived V3 experiment configuration on a dedicated CARLA server.')
    parser.add_argument('--job-id')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    runs = json.loads((ROOT / 'reproducibility/run_index.json').read_text())
    if args.list:
        for run in runs:
            print(run['job_id'])
        return
    matches = [run for run in runs if run['job_id'] == args.job_id]
    if len(matches) != 1:
        parser.error('Choose an exact --job-id from --list.')
    config = load_config(matches[0]['config'])
    if not args.execute:
        print(json.dumps({'job': matches[0], 'execution_requested': False}, indent=2))
        return
    checkpoint = config['artifacts']['rl_checkpoint']
    checkpoint_path = Path(checkpoint['absolute_path'])
    if not checkpoint_path.exists():
        parser.error('The exact checkpoint is withheld pending redistribution permission. See checkpoints/README.md.')
    if sha256(checkpoint_path) != checkpoint['sha256']:
        parser.error('Checkpoint checksum does not match the paper artifact.')
    ensure_hash_seed(config)
    from engine import execute
    lock_path = ROOT / 'generated' / ('carla_port_%s.lock' % config['simulation']['port'])
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('w') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        run_dir, manifest = execute(config, force=True)
    print(run_dir.relative_to(ROOT), manifest['status'])
    if manifest['status'] not in {'passed', 'passed_with_warnings'}:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
