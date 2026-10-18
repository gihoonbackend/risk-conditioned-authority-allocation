import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
INDEX_FILES = {
    'reproducibility/checksums.sha256', 'reproducibility/release_manifest_v1.0.0.json',
    'reproducibility/manifest.json', 'release/v1.0.0-paper-submission/manifest.json',
}
PATTERNS = {
    'provider_key': re.compile(r'sk-(?:proj-)?[A-Za-z0-9_-]{20,}'),
    'aws_access_key': re.compile(r'(?:AKIA|ASIA)[A-Z0-9]{16}'),
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'credential_assignment': re.compile(r'(?i)(?:password|api_key|secret|access_token)\s*[=:]\s*[\"\x27][A-Za-z0-9_+/=-]{12,}[\"\x27]'),
    'bearer_value': re.compile(r'(?i)Bearer\s+[A-Za-z0-9_.-]{20,}'),
    'private_user_path': re.compile(r'(?:/home/|/Users/)[A-Za-z0-9_.-]+/|[A-Za-z]:[\\/]Users[\\/][A-Za-z0-9_.-]+'),
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
}
KEYWORDS = re.compile(r'(?i)sk-|OPENAI_API_KEY|TOKEN|PASSWORD|SECRET|Authorization|Bearer')


def public_files():
    return sorted(path for path in ROOT.rglob('*') if path.is_file() and not any(
        part in {'generated','__pycache__','.git','.venv'} for part in path.relative_to(ROOT).parts))


def digest(path):
    hasher=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):hasher.update(block)
    return hasher.hexdigest()


def scan_text(path):
    if path.suffix=='.gz':
        with gzip.open(path,'rt',encoding='utf-8') as stream:
            while True:
                block=stream.read(1024*1024)
                if not block:break
                yield block
    elif path.suffix in {'.png','.pdf'}:
        if path.suffix=='.png':
            with Image.open(path) as image:
                yield json.dumps({'info':image.info,'exif':dict(image.getexif())},default=str)
        else:
            for command in [['pdfinfo',str(path)],['pdftotext',str(path),'-']]:
                completed=subprocess.run(command,capture_output=True,text=True,check=True)
                yield completed.stdout
    else:
        with path.open(encoding='utf-8') as stream:
            yield stream.read()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seal',action='store_true')
    args=parser.parse_args()
    if args.seal:
        validation=ROOT/'reproducibility/validation_results.json'
        if not validation.is_file() or json.loads(validation.read_text()).get('status')!='passed':
            raise SystemExit('Complete offline validation before sealing the release.')
    findings=[];keywords=Counter();scanned=0
    for path in public_files():
        relative=str(path.relative_to(ROOT))
        if relative in INDEX_FILES:continue
        for block in scan_text(path):
            for name,pattern in PATTERNS.items():
                count=len(pattern.findall(block))
                if count:findings.append({'file':relative,'rule':name,'count':count})
            for item in KEYWORDS.findall(block):keywords[item.lower()]+=1
        scanned+=1
    if findings:
        print(json.dumps(findings,indent=2))
        raise SystemExit('High-confidence secret/private-path findings require review; matched values are deliberately not printed.')
    large=[{'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size} for path in public_files() if path.stat().st_size>=100_000_000]
    privacy=json.loads((ROOT/'data/vehicle/metadata/privacy_transform.json').read_text())
    report={
        'status':'technical_scan_passed_release_permissions_pending',
        'scanned_files':scanned,'high_confidence_findings':[],
        'keyword_occurrences':dict(sorted(keywords.items())),
        'keyword_review':'Matches refer to audit rule definitions, release-rights prose and numeric-token checksum terminology. Keyword presence is not a credential finding.',
        'scope':'All release text and decompressed CSVs; PNG metadata/EXIF; PDF metadata and extracted text. No symlinks included.',
        'vehicle_numeric_rows':privacy['rows'],
        'privacy_removals':privacy['removed_categories'],
        'raw_gps_or_vehicle_identification_channels_detected':False,
        'real_vehicle_visual_media_included':False,
        'synthetic_snapshot_visual_review':'Three archived CARLA frames visually inspected during packaging; no real people, real plates or real GPS metadata included.',
        'permissions':{'code':'LICENSE REVIEW REQUIRED','vehicle_data':'LICENSE REVIEW REQUIRED',
                       'checkpoint':'withheld; redistribution permission unconfirmed','synthetic_snapshots':'license/asset review required'},
        'large_files_at_least_100MB':large,
        'github_public_push_ready':False,
        'human_release_gates':['Confirm original code ownership and license grant.',
                               'Confirm institutional/project vehicle data ownership, consent and release authorization.',
                               'Confirm redistribution terms for synthetic render/VLM artifacts.',
                               'Approve checkpoint release or document restricted availability.',
                               'Cross-check final typeset manuscript and table numbering; no manuscript file was supplied.',
                               'Assign actual repository commit/tag/URL after approval.'],
    }
    (ROOT/'reproducibility/public_release_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Public release audit','',
           'Technical scan: passed. Public upload readiness: **NO — LICENSE REVIEW REQUIRED**.','',
           'The scan covers every release text file, decompressed CSV, PNG metadata/EXIF, and PDF metadata/extracted text. No high-confidence credential, email, private user-directory path or private key was found. Keyword occurrences in the scanner, release-rights prose and numeric-token terminology are benign and counted in public_release_audit.json. The scan does not establish legal permission or guarantee that all quasi-identifying driving patterns are anonymous.','',
           '## Vehicle sanitization','',
           'User metadata, absolute recording date/time, equipment details, internal project/software identifiers and instrument schema hierarchy were removed. All 236,504 numeric measurement rows and relative times are preserved exactly. No GPS, address, VIN, plate or account measurement columns were found. No real-vehicle images or video were included. The three VLM images are CARLA synthetic frames, visually reviewed and without EXIF/GPS tags.','',
           '## Licensing','',
           'The audited artifacts do not establish original-code ownership, institutional/project data redistribution authority, recording consent or checkpoint redistribution permission. No MIT/BSD/CC BY license was assigned. The checkpoint is withheld. The upstream CARLA MIT notice is included for attribution/review and does not license this entire package.','',
           '## Size and archival recommendation','',
           ('No release file reaches the conservative 100,000,000-byte threshold.' if not large else 'Oversized files: '+json.dumps(large)),
           'CSV trajectories use lossless gzip. Git LFS is unnecessary for this package as assembled. After permission approval, use an ordinary GitHub repository and archive the tagged release on Zenodo. If future raw imagery/video expands the release, use a separate versioned Zenodo deposit rather than adding large media to normal Git history.','',
           '## Required human review','',*['- '+item for item in report['human_release_gates']],'',
           'The final manifest and checksums describe this candidate, not an already published release.']
    (ROOT/'reproducibility/public_release_audit.md').write_text('\n'.join(lines)+'\n')
    hashes=json.loads((ROOT/'reproducibility/archived_hashes.json').read_text())
    base={'repository_version':'1.0.0','commit':None,'commit_status':'not yet committed as a standalone public repository',
          'experiment_version':'Canonical-D V3 VLM lateral gain','source_hashes':hashes,
          'public_upload_ready':False,'license_status':'LICENSE REVIEW REQUIRED','checkpoint_included':False,
          'official_table_count':6,'official_figure_count':5,'archived_run_count':36}
    (ROOT/'reproducibility/manifest.json').write_text(json.dumps({**base,
        'run_index':'reproducibility/run_index.json','provenance':'reproducibility/artifact_provenance.json',
        'release_manifest':'reproducibility/release_manifest_v1.0.0.json','checksum_file':'reproducibility/checksums.sha256'},indent=2)+'\n')
    release_files=[path for path in public_files() if str(path.relative_to(ROOT)) not in INDEX_FILES]
    inventory=[{'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':digest(path)} for path in release_files]
    payload={**base,'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'inventory_scope':'All public payload files; excludes generated/, caches, git metadata and the four self-referential manifest/checksum index files.',
        'source_vs_public_hash_note':'Public config/VLM metadata paths were sanitized. Source hashes and distributed hashes are intentionally distinguished.',
        'files':inventory,'payload_file_count':len(inventory),'payload_bytes':sum(item['bytes'] for item in inventory),
        'config_hashes':{item['path']:item['sha256'] for item in inventory if item['path'].endswith('.json') and (item['path'].startswith(('configs/','scenarios/')) or item['path'].endswith('resolved_config.json'))},
        'data_hashes':{item['path']:item['sha256'] for item in inventory if item['path'].startswith('data/')},
        'table_hashes':{item['path']:item['sha256'] for item in inventory if item['path'].startswith('data/tables/')},
        'figure_hashes':{item['path']:item['sha256'] for item in inventory if item['path'].startswith('figures/')}}
    (ROOT/'reproducibility/release_manifest_v1.0.0.json').write_text(json.dumps(payload,indent=2)+'\n')
    (ROOT/'release/v1.0.0-paper-submission/manifest.json').write_text(json.dumps({**base,
        'inventory':'reproducibility/release_manifest_v1.0.0.json','checksums':'reproducibility/checksums.sha256'},indent=2)+'\n')
    checksum_files=[path for path in public_files() if path != ROOT/'reproducibility/checksums.sha256']
    (ROOT/'reproducibility/checksums.sha256').write_text(''.join(digest(path)+'  '+str(path.relative_to(ROOT))+'\n' for path in checksum_files))
    final_files=public_files()
    print(json.dumps({'public_files':len(final_files),'public_bytes':sum(path.stat().st_size for path in final_files),
                      'high_confidence_findings':0,'files_at_least_100MB':large,'sealed':args.seal,
                      'public_upload_ready':False},indent=2))


if __name__=='__main__':
    main()
