import contextlib
import os
import subprocess
import sys
import sysconfig

import twisted.scripts.trial


def run():

    envbindir = sysconfig.get_path("scripts")

    # with subprocess.Popen(
    #     [os.path.join(envbindir, "subunit-1to2")],
    #     stdin=subprocess.PIPE,
    #     stdout=subprocess.PIPE,
    # ) as subunit_1to2:
    #     with open(os.environ["JUNITXML_PATH"], "w") as f:
    #         subprocess.Popen(
    #             [os.path.join(envbindir, "subunit2junitxml")],
    #             stdin=subunit_1to2.stdout,
    #             stdout=f,
    #         )

    #         subprocess.run(envbin)
    with open("/dev/null", "w") as f:
        with contextlib.redirect_stdout(f):
            with contextlib.redirect_stderr(f):
                # sys.argv.insert(1, "--reporter=subunit")
                sys.stdout = f
                twisted.scripts.trial.run()
