# -*- coding: utf-8 -*-
"""
Module for running the production http server
"""

from views import APP as application

if __name__ == "__main__":
    application.run()
