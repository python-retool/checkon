import sys

import twisted.scripts.trial


def run():
    sys.argv.insert(1, "--reporter=subunit")
    twisted.scripts.trial.run()
