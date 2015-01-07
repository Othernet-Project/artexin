"""
app.py: Main application module
"""

from __future__ import unicode_literals

import os
import sys
import logging
from logging.config import dictConfig as log_config

import bottle

PKGDIR = os.path.dirname(__file__)
PROJDIR = os.path.dirname(PKGDIR)
VIEWDIR = os.path.join(PKGDIR, 'views')
CONFPATH = os.path.join(PKGDIR, 'artexin.ini')
sys.path.insert(0, PROJDIR)

from artexin_webui.utils import squery, migrations


app = bottle.default_app()

bottle.TEMPLATE_PATH.insert(0, VIEWDIR)


def main(conf=CONFPATH):
    app.config.load_config(conf)

    # Install database plugin
    app.install(squery.database_plugin)

    config = app.config  # alias for easy access

    # Configure logging
    log_config({
        'version': 1,
        'root': {
            'handlers': ['file'],
            'level': logging.DEBUG,
        },
        'handlers': {
            'file': {
                'class' : 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': config['logging.output'],
                'maxBytes': int(config['logging.size']),
                'backupCount': int(config['logging.backups'])
            },
        },
        'formatters': {
            'default': {
                'format' : config['logging.format'],
                'datefmt' : config['logging.date_format']
            },
        },
    })

    # Migrations
    db = squery.Database(config['database.path'])
    migrations.migrate(db, os.path.join(PKGDIR, 'migrations'))
    logging.debug("Finished running migrations")
    db.disconnect()

    # Start the server
    bottle.debug(True)
    bottle.run(app)


if __name__ == '__main__':
    main()

