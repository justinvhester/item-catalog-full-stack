import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/discr/vagrant/catalog/")

activate_this = '/var/www/discr/vagrant/catalog/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from application import app as application
application.config.from_pyfile('config.py')
if __name__ == '__main__':
    application.run()
