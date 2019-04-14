from setuptools import setup, find_packages

setup(
    name='toolbelt',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'asn1crypto==0.24.0', 'bcrypt==3.1.4', 'cffi==1.11.5', 'click==6.7', 'cryptography==2.3.1', 'dominate==2.3.1', 'filelock==3.0.10', 'flake8==3.6.0', 'Flask==1.0.2', 'Flask-API==1.1', 'Flask-Bcrypt==0.7.1', 'Flask-Bootstrap==3.3.7.1', 'Flask-Cors==3.0.6', 'Flask-Login==0.4.1', 'Flask-SQLAlchemy==2.3.2', 'Flask-WTF==0.14.2', 'gitdb2==2.0.5', 'GitPython==2.1.11', 'idna==2.7', 'itsdangerous==0.24', 'Jinja2==2.10', 'MarkupSafe==1.0', 'mccabe==0.6.1', 'nose==1.3.7', 'packaging==18.0', 'pbkdf2==1.3', 'pluggy==0.8.0', 'psutil==5.5.0', 'py==1.7.0', 'pycodestyle==2.4.0', 'pycparser==2.18', 'pyflakes==2.0.0', 'pyparsing==2.3.0', 'python-dateutil==2.7.5', 'Send2Trash==1.5.0', 'six==1.11.0', 'smmap2==2.0.5', 'SQLAlchemy==1.2.11', 'toml==0.10.0', 'tox==3.5.3', 'virtualenv==16.1.0', 'visitor==0.1.3', 'Werkzeug==0.14.1', 'wifi==0.3.8', 'WTForms==2.2.1'
    ]
)
