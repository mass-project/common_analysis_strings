from setuptools import setup, find_packages
from common_analysis_strings import __version__

setup(
    name="common_analysis_strings",
    version=__version__,
    packages=find_packages(),
    install_requires=[
        'common_analysis_base',
        'common_helper_files'
    ]
)
