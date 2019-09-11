import setuptools


setuptools.setup(
    name="checkon-trial",
    description="Patch for trial to ensure subunit reporting.",
    version="0.0.2",
    packages=["checkon_trial"],
    entry_points={"console_scripts": ["trial = checkon_trial.checkon_trial:run"]},
    install_requires=["python-subunit", "twisted", "junitxml"],
)
