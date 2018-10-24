#!/usr/bin/env python
import os
from migrate.versioning.shell import main

if __name__ == "__main__":
    main(repository="migrations", url=os.environ["DATABASE_URI"], debug="False")
