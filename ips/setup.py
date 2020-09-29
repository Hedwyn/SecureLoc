from setuptools import setup, find_packages
import os

## dependencies
REQUIREMENTS = "requirements.txt"
LIB_FOLDER = os.path.dirname(os.path.realpath(__file__))
REQ_PATH = LIB_FOLDER + "/" + REQUIREMENTS
if os.path.isfile(REQ_PATH):
    with open(REQ_PATH) as f:
        install_reqs = list(f.read().splitlines())
else:
    print("Requirements could not be found")
    install_reqs = ""

# installing
setup(
    name='ips', 
    version='1.0', 
    author = "Baptiste Pestourie",
    description = "Indoor Positioning Engine for DecaWino UWB chips",
    url = "https://github.com/Hedwyn/SecureLoc",
    packages = find_packages(),
    install_requires = install_reqs,
    classifier = ["Programming Language :: Python :: 3", "License: GPL v3"],
    python_requires = '>=3.6')



