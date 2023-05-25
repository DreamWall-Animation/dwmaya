import os
import tempfile
import subprocess


def launch_mayapy_script(
        mayapypath=None, script=None, scriptpath=None, environment=None,
        arguments=None, capture_output=True):
    arguments = arguments or []
    if script:
        scriptpath = f'{tempfile.NamedTemporaryFile().name}.py'
        with open(scriptpath, 'w') as f:
            f.write(script)
            print(scriptpath)
    elif scriptpath is None:
        raise ValueError('Please specify at least a script or a script path')
    return subprocess.run(
        [mayapypath or 'mayapy', scriptpath] + arguments,
        env=environment or os.environ.copy(),
        capture_output=capture_output)
