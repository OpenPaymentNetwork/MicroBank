
from microbank.models import appmaker
from pyramid.config import Configurator
from sqlalchemy import engine_from_config


def main(global_config, **settings):
    """ This function returns a WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    get_root = appmaker(engine)
    config = Configurator(settings=settings, root_factory=get_root)
    config.add_static_view('static', 'microbank:static', cache_max_age=3600)
    config.add_static_view('static-deform', 'deform:static')
    config.scan('microbank.views')
    return config.make_wsgi_app()
