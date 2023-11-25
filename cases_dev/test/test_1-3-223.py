import subprocess
import sys
def check(name):
    latest_version = str(subprocess.run(
        [sys.executable, '-m', 'pip', 'install',
         '{}==random'.format(name)],
        capture_output=True, text=True))
    latest_version = latest_version[
                     latest_version.find('(from versions:')+15:]
    latest_version = latest_version[:latest_version.find(')')]
    latest_version = latest_version.replace(' ','').split(',')[-1]
    current_version = str(subprocess.run(
        [sys.executable, '-m', 'pip', 'show', '{}'.format(name)],
        capture_output=True, text=True))
    current_version = current_version[
                      current_version.find('Version:')+8:]
    current_version = current_version[:current_version.find('\\n')].replace(' ','')
    if latest_version == current_version:
        return True
    else:
        return False


assert checkVersion('numpy') == check('numpy')
assert checkVersion('torch') == check('torch')
assert checkVersion('torchvision') == check('torchvision')
assert checkVersion('matplotlib') == check('matplotlib')
assert checkVersion('scipy') == check('scipy')
