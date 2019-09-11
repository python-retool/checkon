import contextlib
import os
import subprocess
import sys
import sysconfig


def run():

    envbindir = sysconfig.get_path("scripts")

    with subprocess.Popen(
        [os.path.join(envbindir, "subunit-1to2")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    ) as subunit_1to2:
        with open(os.environ["JUNITXML_PATH"], "w") as f:
            subprocess.Popen(
                [os.path.join(envbindir, "subunit2junitxml")],
                stdin=subunit_1to2.stdout,
                stdout=f,
            )

            with contextlib.redirect_stdout(subunit_1to2.stdin):
                sys.argv.insert(1, "--reporter=subunit")
                import twisted.scripts.trial

                twisted.scripts.trial.run()
