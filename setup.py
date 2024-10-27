from setuptools import setup, find_packages

setup(
    name='flux_orm',
    version='0.1',
    packages=find_packages(),
    url='https://github.com/FluxFury/flux-orm',
    install_requires=[
        "python",
        "fastapi",
        "pydantic",
        "SQLAlchemy",
        "uvicorn",
        "python-dotenv",
        "asyncpg",
        "uuid6",
        "setuptools",
        "pytest-sqlalchemy",
        "pytest-asyncio"
    ],

)
