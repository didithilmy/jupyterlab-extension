from notebook.utils import url_path_join
from .instances import InstancesHandler
from .did_browser import DIDBrowserHandler
from .did_details import DIDDetailsHandler
from .did_make_available import DIDMakeAvailableHandler
from rucio_jupyterlab.config import RucioConfig, Config
from rucio_jupyterlab.rucio import RucioAPIFactory


def setup_handlers(web_app):
    host_pattern = ".*$"

    rucio_config = RucioConfig(config=web_app.settings['config'])
    config = Config(rucio_config)
    rucio_factory = RucioAPIFactory(config=config)

    handler_params = dict(rucio_config=config, rucio=rucio_factory)

    base_url = web_app.settings["base_url"]
    base_path = url_path_join(base_url, 'rucio-jupyterlab')
    handlers = [
        (url_path_join(base_path, 'instances'), InstancesHandler, handler_params),
        (url_path_join(base_path, 'files'), DIDBrowserHandler, handler_params),
        (url_path_join(base_path, 'did'), DIDDetailsHandler, handler_params),
        (url_path_join(base_path, 'did', 'make-available'),
         DIDMakeAvailableHandler, handler_params),
    ]
    web_app.add_handlers(host_pattern, handlers)
