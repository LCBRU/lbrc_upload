#!/usr/bin/env python
from migrate.versioning.shell import main
from dotenv import load_dotenv

load_dotenv()

from config import Config

if __name__ == "__main__":
    main(repository="migrations", url=Config.SQLALCHEMY_DATABASE_URI, debug="True")
