#!/usr/bin/env python3

from upload import create_app
from config import LiveConfig

application = create_app(LiveConfig())
