from setuptools import setup

setup(
    name="asmp",
    version="0.1.0",
    description="ASMP - ArtStudia Manager Packets",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="ArtTeam",
    author_email="ArtRebos@gmail.com",
    url="https://github.com/artteam09/asmp",
    py_modules=["asmp"],
    entry_points={
        'console_scripts': [
            'asp=asmp:main',
        ],
    },
    install_requires=[
        'requests>=2.25.0',
        'colorama>=0.4.6'
    ],
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    keywords='package manager, artstudia, asmp, packages',
    project_urls={
        'Homepage': 'https://github.com/artteam09/asmp',
        'Repository': 'https://github.com/artteam09/asmp',
        'Bug Reports': 'https://github.com/artteam09/asmp/issues',
    },
)