from setuptools import setup, find_packages

setup(
    name='flux_orm',  # This is the name you'll use to reference the project
    version='0.1',
    packages=find_packages(),
    url='https://github.com/FluxFury/flux-orm',
    install_requires=[
        # List your project dependencies here, e.g., SQLAlchemy, etc.
    ],
    entry_points={
        'console_scripts': [
            # Optionally add console scripts if you have executable scripts
        ],
    },
)
