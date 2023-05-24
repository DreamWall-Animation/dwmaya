import os
import sys
import tempfile
import subprocess


def copy_current_environment():
    pythonpaths = os.environ["PYTHONPATH"].split(os.pathsep)
    pythonpaths = [p.replace("\\", "/") for p in pythonpaths]
    for path in sys.path:
        path = path.replace("\\", "/")
        if path in pythonpaths:
            continue
        pythonpaths.append(path)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(os.pathsep.join(pythonpaths))
    return environment


def launch_mayapy_script(
        mayapypath=None, script=None, scriptpath=None, environment=None,
        arguments=None):
    arguments = arguments or []
    if script:
        scriptpath = f'{tempfile.NamedTemporaryFile().name}.py'
        with open(scriptpath, 'w') as f:
            f.write(script)
            print(scriptpath)
    elif scriptpath is None:
        raise ValueError('Please specify at least a script or a script path')
    environment = environment or copy_current_environment()
    return subprocess.Popen(
        [mayapypath or 'mayapy', scriptpath] + arguments,
        env=environment,
        bufsize=-1)