#!/usr/bin/env python3
"""Execute the real entry point against a disposable Unraid command contract."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
# GNU date/stat are part of Unraid and the Ubuntu runner. macOS can use coreutils.
GNU = Path('/opt/homebrew/opt/coreutils/libexec/gnubin')
SYSTEM_PATH = f'{GNU}:{os.defpath}' if GNU.exists() else os.defpath

ADAPTER = '''#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys
p = pathlib.Path(os.environ['FIXTURE_ROOT'])
step = int((p / 'step').read_text())
scenario = os.environ['FIXTURE_SCENARIO']
name = pathlib.Path(sys.argv[0]).name
if name == 'curl':
    assert sys.argv[-1] == 'https://api.github.com/repos/edbfi/mover-status/releases'
    print('[{"tag_name":"0.1.0"}]')
elif name == 'pgrep':
    active = step in (1, 2, 3)
    pattern = sys.argv[-1]
    match = pattern == ('mover' if scenario == 'du' else 'age_mover')
    if active and match:
        print('424242')
    else:
        sys.exit(1)
elif name == 'stat':
    if sys.argv[-1] == '/proc/424242':
        print('1700000000')
    else:
        sys.exit(subprocess.call([os.environ['FIXTURE_STAT'], *sys.argv[1:]]))
elif name == 'date':
    if sys.argv[1:] == ['+%s']:
        print(1700000000 + step * 5)
    else:
        sys.exit(subprocess.call([os.environ['FIXTURE_DATE'], *sys.argv[1:]]))
elif name == 'du':
    assert sys.argv[1:] == ['-sb', str(p / 'cache')]
    print(str(1000 if step < 3 else (500 if step == 3 else 0)) + '\\t' + str(p / 'cache'))
elif name == 'sleep':
    step += 1
    (p / 'step').write_text(str(step))
    if scenario != 'du':
        if step == 1 and scenario == 'missing':
            pass
        elif step == 1 and scenario == 'malformed':
            (p / 'mover.ini').write_text('TotalToSecondary=oops\\nRemainToSecondary=900\\n')
        else:
            remain = 1000 if step < 3 else (500 if step == 3 else 0)
            (p / 'mover.ini').write_text(f'TotalToSecondary=1000\\nRemainToSecondary={remain}\\nTotalFilesToSecondary=10\\nRemainFilesToSecondary={remain // 100}\\nFile=/synthetic/file\\n')
    # Bound even a broken application loop without a busy spin.
    import time
    time.sleep(0.05)
elif name == 'notify':
    with (p / 'notifications.jsonl').open('a') as f:
        f.write(json.dumps(sys.argv[1:]) + '\\n')
    sys.exit(1 if scenario == 'notify-error' else 0)
else:
    raise RuntimeError(name)
'''


class RuntimeContract(unittest.TestCase):
    def run_case(self, scenario):
        with tempfile.TemporaryDirectory(prefix='mover-contract-') as directory:
            p = Path(directory)
            (p / 'bin').mkdir()
            (p / 'cache').mkdir()
            (p / 'step').write_text('0')
            for name in ('curl', 'pgrep', 'stat', 'date', 'du', 'sleep', 'notify'):
                tool = p / 'bin' / name
                tool.write_text(ADAPTER)
                tool.chmod(0o700)
            env = {
                'PATH': f'{p / "bin"}:{Path(shutil.which("python3")).parent}:{SYSTEM_PATH}',
                'FIXTURE_ROOT': str(p), 'FIXTURE_SCENARIO': scenario,
                'FIXTURE_DATE': shutil.which('date', path=SYSTEM_PATH),
                'FIXTURE_STAT': shutil.which('stat', path=SYSTEM_PATH),
                'MOVER_STATUS_USE_UNRAID': 'true',
                'MOVER_STATUS_NOTIFY_BIN': str(p / 'bin' / 'notify'),
                'MOVER_STATUS_DEBUG': 'true', 'MOVER_STATUS_POLL_INTERVAL': '1',
                'MOVER_STATUS_CACHE_PATH': str(p / 'cache'),
                'MOVER_STATUS_INI_PATH': str(p / 'mover.ini'),
                'MOVER_STATUS_STATE_DIR': str(p / 'state'),
            }
            if scenario == 'bad-cache':
                env['MOVER_STATUS_CACHE_PATH'] = str(p / 'absent')
            with (p / 'output').open('w') as output:
                proc = subprocess.Popen(['bash', str(ROOT / 'moverStatus.sh')],
                                        env=env, stdout=output, stderr=subprocess.STDOUT,
                                        start_new_session=True)
                try:
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        text = (p / 'output').read_text()
                        if 'Restarting monitoring after completion' in text or proc.poll() is not None:
                            break
                        time.sleep(0.02)
                    else:
                        self.fail('entry point exceeded 10-second deadline:\n' + text)
                    if scenario == 'bad-cache':
                        self.assertEqual(proc.wait(timeout=2), 1)
                    else:
                        self.assertIsNone(proc.poll(), text)
                finally:
                    try:
                        os.killpg(proc.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    proc.wait(timeout=2)
            text = (p / 'output').read_text()
            notifications = [json.loads(line) for line in
                             (p / 'notifications.jsonl').read_text().splitlines()] \
                if (p / 'notifications.jsonl').exists() else []
            stats = (p / 'state' / 'last-run').read_text() \
                if (p / 'state' / 'last-run').exists() else ''
            self.assertFalse((p / 'state' / 'state').exists(), text)
            return text, notifications, stats

    def test_running_and_completion(self):
        for scenario in ('normal', 'missing', 'malformed', 'du', 'notify-error'):
            with self.subTest(scenario=scenario):
                text, notifications, stats = self.run_case(scenario)
                self.assertIn('Mover process not found, waiting', text)
                self.assertIn('Mover process found, starting', text)
                self.assertIn('percent=50, moved=500, remaining=500, total=1000', text)
                self.assertIn('MOVED_BYTES=1000', stats)
                self.assertIn('TOTAL_BYTES=1000', stats)
                payloads = json.dumps(notifications)
                self.assertIn('50% complete', payloads)
                self.assertIn('Moving has been completed!', payloads)
                self.assertNotIn('{percent}', payloads)
                if scenario in ('missing', 'malformed'):
                    self.assertIn('preparing/scanning', text)
                    self.assertIn('Fresh mover.ini detected', text)
                if scenario == 'notify-error':
                    self.assertIn('Warning: Final direct notification had a delivery failure.', text)

    def test_missing_cache_fails_before_notification(self):
        text, notifications, stats = self.run_case('bad-cache')
        self.assertIn('Error: CACHE_PATH directory does not exist', text)
        self.assertEqual(notifications, [])
        self.assertEqual(stats, '')


if __name__ == '__main__':
    unittest.main()
