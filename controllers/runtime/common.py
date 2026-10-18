import copy
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / 'configs/canonical_d_v3/resolved_config.json'


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def json_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_safe(item) for item in value]
    return value


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(json_safe(value), indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def git_provenance():
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        status = subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        commit, status = None, 'source archive without git metadata'
    return {'commit': commit, 'status': status}


def load_config(path=DEFAULT_CONFIG, scenario=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    config = copy.deepcopy(json.loads(path.read_text()))
    if 'extends' in config:
        overlay = config
        config = load_config(path.parent / overlay['extends'], scenario)
        def merge(target, additions):
            for key, value in additions.items():
                if isinstance(value, dict) and isinstance(target.get(key), dict):
                    merge(target[key], value)
                else:
                    target[key] = value
        merge(config, overlay.get('overrides', {}))
        config['config_version'] = overlay['config_version']
    if scenario is not None:
        if scenario != config['experiment']['scenario']:
            raise ValueError('Select the matching archived scenario config; changing its name alone is not supported.')
    risk = config['risk']
    expected = {'formulation': 'NORMALIZED', 'active_weight_policy': 'RENORMALIZED',
                'alpha_component_mode': 'all', 'separate_risk_definition': 'channel_normalized',
                'separate_lateral_vlm_gain_policy': 'normalized_path_max', 'R_th': 0.5, 'k': 5.0}
    for key, value in expected.items():
        if risk[key] != value:
            raise ValueError('Public V3 contract mismatch: ' + key)
    for name, item in config['artifacts'].items():
        artifact = ROOT / item['relative_path']
        item['absolute_path'] = str(artifact)
        if artifact.exists() and sha256(artifact) != item['sha256']:
            raise ValueError('Artifact checksum mismatch: ' + name)
        if name != 'rl_checkpoint' and not artifact.is_file():
            raise FileNotFoundError(artifact)
    output = (ROOT / config['experiment']['output_root']).resolve()
    if ROOT / 'generated' not in output.parents:
        raise ValueError('New run output must stay under generated/')
    return config


def source_hashes():
    paths = []
    for folder in ('controllers', 'scripts'):
        paths.extend(path for path in (ROOT / folder).rglob('*') if path.suffix in {'.py', '.cpp', '.hpp'})
    return {str(path.relative_to(ROOT)): sha256(path) for path in sorted(paths)}


def build_library(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    library = output_dir / 'librevision_controller.so'
    sources = ['controllers/runtime/controller_bridge.cpp', 'controllers/ctg/longitudinal_ctg.cpp',
               'controllers/mpc/longitudinal_mpc.cpp', 'controllers/lqr/lateral_lqr.cpp']
    command = ['g++', '-O2', '-std=c++17', '-fPIC', '-shared', '-I' + str(ROOT / 'controllers/include'),
               *[str(ROOT / path) for path in sources], '-o', str(library)]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    (output_dir / 'build.log').write_text(result.stdout + result.stderr)
    return library, {'command': command, 'compiler': subprocess.check_output(['g++', '--version'], text=True).splitlines()[0],
                     'library_sha256': sha256(library)}


def import_carla():
    return importlib.import_module('carla')


def ensure_hash_seed(config):
    expected = str(config['experiment']['python_hash_seed'])
    if os.environ.get('PYTHONHASHSEED') != expected:
        environment = os.environ.copy()
        environment['PYTHONHASHSEED'] = expected
        os.execve(sys.executable, [sys.executable, *sys.argv], environment)
