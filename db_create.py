#! venv/bin/python

from migrate.versioning import api
#from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO
from app import db
import os.path

db.create_all()

