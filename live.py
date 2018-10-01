#!/usr/bin/env python3

from upload import create_app
from config import LiveConfig

app = create_app(LiveConfig())
