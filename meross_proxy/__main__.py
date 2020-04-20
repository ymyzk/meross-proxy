import os

from meross_iot.manager import MerossManager
from prometheus_client import make_wsgi_app

from meross_proxy.app import make_bottle_app


HOST = os.environ.get("PROXY_HOST", "localhost")
PORT = int(os.environ.get("PROXY_PORT", "8080"))
EMAIL = os.environ.get("MEROSS_EMAIL")
PASSWORD = os.environ.get("MEROSS_PASSWORD")


manager = MerossManager.from_email_and_password(
    meross_email=EMAIL, meross_password=PASSWORD,
)
make_bottle_app(
    meross_manager=manager,
    prometheus_app=make_wsgi_app(),
).run(host=HOST, port=PORT)
