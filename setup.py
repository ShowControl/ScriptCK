try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'ScriptCK',
    'author': 'bapril',
    'url': 'URL to get it at.',
    'download_url': 'Where to download it.',
    'author_email': 'My email.',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['script_ck'],
    'scripts': [],
    'name': 'script_ck'
}

setup(**config)
