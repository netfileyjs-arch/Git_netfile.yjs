# -*- coding: utf-8 -*-
"""
HeyGen API로 넷파일 회원가입 유도 영상을 일괄 생성하는 스크립트
(표준 라이브러리만 사용 - 별도 설치 불필요)

사용 예:
    python heygen_generate.py voices --lang Korean      # 한국어 음성 목록
    python heygen_generate.py avatars --search Daisy    # 아바타 검색
    python heygen_generate.py render --dry-run          # API 호출 없이 요청 내용 확인
    python heygen_generate.py render --only A_hook_weekend --test
    python heygen_generate.py status <video_id> --download

API 키는 환경변수 HEYGEN_API_KEY 로 전달합니다.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = os.environ.get('HEYGEN_API_BASE', 'https://api.heygen.com')
HERE = Path(__file__).resolve().parent
PLACEHOLDER = re.compile(r'\{\{\s*([^}]+?)\s*\}\}')

# 화면 비율별 1080p 해상도 (--resolution 720 이면 2/3로 축소)
ASPECTS = {
    '9:16': (1080, 1920),
    '16:9': (1920, 1080),
    '1:1': (1080, 1080),
}


def api_request(method, path, body=None):
    """HeyGen API 호출 후 JSON 응답 반환"""
    api_key = os.environ.get('HEYGEN_API_KEY')
    if not api_key:
        sys.exit('❌ 환경변수 HEYGEN_API_KEY 가 없습니다. HeyGen 설정 > API 에서 키를 발급받아 지정하세요.')

    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(
        API_BASE + path,
        data=data,
        method=method,
        headers={
            'X-Api-Key': api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')
        sys.exit(f'❌ HeyGen API 오류 {e.code} ({method} {path}): {detail}')
    except urllib.error.URLError as e:
        sys.exit(f'❌ HeyGen API 연결 실패 ({method} {path}): {e.reason}')


def is_unset(value):
    return value is None or str(value).strip() == '' or str(value).startswith('TODO')


def resolve(text, variables):
    """{{변수}}를 치환하고, 값이 비어 있거나 TODO인 변수 이름을 함께 반환"""
    missing = set()

    def sub(match):
        key = match.group(1)
        value = variables.get(key)
        if is_unset(value):
            missing.add(key)
            return match.group(0)
        return str(value)

    return PLACEHOLDER.sub(sub, text), missing


def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_payload(video, config, resolution, test):
    """videos.json 의 영상 1개를 HeyGen /v2/video/generate 요청 본문으로 변환"""
    defaults = config.get('defaults', {})
    variables = config.get('variables', {})
    missing = set()

    if video.get('aspect') not in ASPECTS:
        sys.exit(f"❌ {video.get('id')}: aspect 는 {', '.join(ASPECTS)} 중 하나여야 합니다.")
    width, height = ASPECTS[video['aspect']]
    if resolution == 720:
        width, height = width * 2 // 3, height * 2 // 3

    video_inputs = []
    for scene in video['scenes']:
        # 씬 > 영상 > 기본값 순으로 설정을 찾는다
        def pick(key):
            for source in (scene, video, defaults):
                if key in source:
                    return source[key]
            return None

        text, scene_missing = resolve(scene['text'], variables)
        missing |= scene_missing

        avatar_id, voice_id = pick('avatar_id'), pick('voice_id')
        if is_unset(avatar_id):
            missing.add('defaults.avatar_id')
        if is_unset(voice_id):
            missing.add('defaults.voice_id')

        video_inputs.append({
            'character': {
                'type': 'avatar',
                'avatar_id': avatar_id,
                'avatar_style': pick('avatar_style') or 'normal',
            },
            'voice': {
                'type': 'text',
                'input_text': text,
                'voice_id': voice_id,
                'speed': pick('speed') or 1.0,
            },
            'background': {
                'type': 'color',
                'value': pick('background') or '#000000',
            },
        })

    payload = {
        'title': f"[넷파일] {video['id']} - {video['title']}",
        'video_inputs': video_inputs,
        'dimension': {'width': width, 'height': height},
        'caption': bool(video.get('caption', defaults.get('caption', True))),
        'test': test,
    }
    return payload, missing


def wait_for_video(video_id, interval=15, timeout=1800):
    """렌더링 완료까지 상태 조회 후 최종 data 반환"""
    deadline = time.time() + timeout
    while True:
        data = api_request('GET', f'/v1/video_status.get?video_id={video_id}').get('data') or {}
        status = data.get('status')
        if status in ('completed', 'failed'):
            return data
        if time.time() > deadline:
            print(f'   ⏱️ {video_id}: {timeout // 60}분 안에 끝나지 않았습니다. 나중에 status 명령으로 확인하세요.')
            return data
        print(f'   … {video_id}: {status}')
        time.sleep(interval)


def download(data, out_dir, name):
    """완료된 영상(및 자막 입힌 버전)을 out_dir 에 저장"""
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for key, suffix in (('video_url', ''), ('video_url_caption', '_caption')):
        url = data.get(key)
        if url:
            target = out_dir / f'{name}{suffix}.mp4'
            urllib.request.urlretrieve(url, target)
            saved.append(target)
    return saved


def cmd_voices(args):
    voices = api_request('GET', '/v2/voices').get('data', {}).get('voices', [])
    lang = (args.lang or '').lower()
    rows = [v for v in voices if lang in str(v.get('language', '')).lower()]
    for v in rows:
        print(f"{v.get('voice_id')}\t{v.get('name')}\t{v.get('gender')}\t{v.get('language')}")
    print(f'\n총 {len(rows)}개. 미리듣기는 HeyGen 웹에서 이름으로 검색해 확인하세요.')


def cmd_avatars(args):
    avatars = api_request('GET', '/v2/avatars').get('data', {}).get('avatars', [])
    term = (args.search or '').lower()
    rows = [a for a in avatars if term in str(a.get('avatar_name', '')).lower()]
    for a in rows:
        print(f"{a.get('avatar_id')}\t{a.get('avatar_name')}\t{a.get('gender')}")
    print(f'\n총 {len(rows)}개.')


def cmd_render(args):
    config = load_config(args.config)
    videos = config['videos']
    if args.only:
        unknown = set(args.only) - {v['id'] for v in videos}
        if unknown:
            sys.exit(f"❌ videos.json 에 없는 id: {', '.join(sorted(unknown))}")
        videos = [v for v in videos if v['id'] in args.only]

    jobs = []
    blocked = False
    for video in videos:
        payload, missing = build_payload(video, config, args.resolution, args.test)
        if missing:
            blocked = True
            print(f"⚠️ {video['id']}: 아직 채우지 않은 값 → {', '.join(sorted(missing))}")
        if args.dry_run:
            print(f"\n=== {video['id']} ===")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            continue
        jobs.append((video, payload))

    if args.dry_run:
        return
    if blocked:
        sys.exit('❌ videos.json 의 TODO 값을 실제 내용으로 채운 뒤 다시 실행하세요. (확인되지 않은 혜택 문구로 광고가 나가는 것을 막기 위함)')

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / 'jobs.json'
    log = json.loads(log_path.read_text(encoding='utf-8')) if log_path.exists() else {}

    submitted = []
    for video, payload in jobs:
        result = api_request('POST', '/v2/video/generate', payload)
        video_id = (result.get('data') or {}).get('video_id')
        if not video_id:
            sys.exit(f"❌ {video['id']}: video_id 를 받지 못했습니다. 응답: {result}")
        print(f"🎬 {video['id']} 생성 요청 완료 → video_id={video_id}")
        log[video['id']] = {'video_id': video_id, 'test': args.test, 'submitted_at': time.strftime('%Y-%m-%d %H:%M:%S')}
        submitted.append((video['id'], video_id))
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')

    if args.no_wait:
        print(f'\n요청 기록: {log_path}  (나중에 status 명령으로 확인)')
        return

    for name, video_id in submitted:
        data = wait_for_video(video_id)
        if data.get('status') == 'completed':
            for path in download(data, out_dir, name):
                print(f'✅ {name}: {path}')
        elif data.get('status') == 'failed':
            print(f"❌ {name}: 렌더링 실패 → {data.get('error')}")


def cmd_status(args):
    data = api_request('GET', f'/v1/video_status.get?video_id={args.video_id}').get('data') or {}
    print(json.dumps(data, ensure_ascii=False, indent=2))
    if args.download and data.get('status') == 'completed':
        for path in download(data, Path(args.out), args.video_id):
            print(f'✅ 저장: {path}')


def main():
    parser = argparse.ArgumentParser(description='HeyGen API로 넷파일 회원가입 유도 영상 생성')
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('voices', help='음성 목록 (voice_id 확인)')
    p.add_argument('--lang', default='Korean', help='언어 필터 (기본: Korean, 전체는 "")')
    p.set_defaults(func=cmd_voices)

    p = sub.add_parser('avatars', help='아바타 목록 (avatar_id 확인)')
    p.add_argument('--search', help='아바타 이름 검색어')
    p.set_defaults(func=cmd_avatars)

    p = sub.add_parser('render', help='videos.json 대본으로 영상 생성')
    p.add_argument('--config', default=str(HERE / 'videos.json'))
    p.add_argument('--only', nargs='+', metavar='ID', help='특정 영상 id만 생성')
    p.add_argument('--test', action='store_true', help='워터마크 테스트 영상으로 생성 (크레딧 절약용)')
    p.add_argument('--dry-run', action='store_true', help='API 호출 없이 요청 본문만 출력')
    p.add_argument('--resolution', type=int, choices=(1080, 720), default=1080,
                   help='요금제가 1080p를 지원하지 않으면 720')
    p.add_argument('--no-wait', action='store_true', help='생성 요청만 하고 완료를 기다리지 않음')
    p.add_argument('--out', default=str(HERE / 'output'))
    p.set_defaults(func=cmd_render)

    p = sub.add_parser('status', help='video_id 상태 확인')
    p.add_argument('video_id')
    p.add_argument('--download', action='store_true', help='완료된 영상이면 내려받기')
    p.add_argument('--out', default=str(HERE / 'output'))
    p.set_defaults(func=cmd_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
