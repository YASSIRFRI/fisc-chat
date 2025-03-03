from setuptools import setup, find_packages

setup(
    name="law_text_preprocessor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyMuPDF>=1.21.1",
        "regex>=2022.1.18",
        "pathlib>=1.0.1",
    ],
    entry_points={
        'console_scripts': [
            'process_law=src.main:main',
        ],
    },
    author="AI Assistant",
    author_email="example@example.com",
    description="A preprocessor for law texts in PDF format",
)