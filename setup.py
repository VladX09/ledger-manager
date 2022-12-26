import os

from setuptools import find_packages, setup


def parse_requirements(requirements_file: str):
    requirements_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), requirements_file)

    with open(requirements_path, "r") as fp:
        return list(fp.readlines())


setup(
    name="ledger-manager",
    version="0.1.0",
    description="Ledger CLI wrapper with additional tools",
    author="Vladislav Verba",
    author_email='vladoladis@gmail.com',
    packages=find_packages(),
    package_data={"ledger_manager": ["*.yml", "*.yaml"]},
    install_requires=parse_requirements("requirements.in"),
    entry_points="""
        [console_scripts]
        ledger-manager=ledger_manager.cli:app
    """,
)
