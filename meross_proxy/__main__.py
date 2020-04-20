import atexit
import os

from bottle import abort, Bottle, request, response, run
from meross_iot.cloud.devices.power_plugs import GenericPlug
from meross_iot.manager import MerossManager
from prometheus_client import make_wsgi_app


HOST = os.environ.get("PROXY_HOST", "localhost")
PORT = int(os.environ.get("PROXY_PORT", "8080"))
EMAIL = os.environ.get("MEROSS_EMAIL")
PASSWORD = os.environ.get("MEROSS_PASSWORD")

prometheus_app = make_wsgi_app()


def plug_to_dict(p):
    return {
        "uuid": p.uuid,
        "name": p.name,
        "online": p.online,
        "fwversion": p.fwversion,
        "status": p.get_status(),
    }


class MerossProxyApp:
    def __init__(self, meross_manager):
        # Initialize Bottle application
        app = Bottle()
        app.route("/healthz", callback=self.healthcheck)
        app.route("/metrics", callback=self.metrics)
        app.route("/plugs", callback=self.list_plugs)
        app.route("/plugs/<uuid:re:[0-9a-f]+>", callback=self.get_plug)
        app.route("/plugs/<uuid:re:[0-9a-f]+>/turn_off",
                  method="POST", callback=self.turn_off_plug)
        app.route("/plugs/<uuid:re:[0-9a-f]+>/turn_on",
                  method="POST", callback=self.turn_on_plug)
        self.app = app

        # Initialize MerossManager
        meross_manager.start()
        atexit.register(lambda: meross_manager.stop())

        # Discover devices
        self.plugs = {d.uuid: d for d in meross_manager.get_devices_by_kind(GenericPlug)}


    def healthcheck(self):
        return {
            "status": "OK",
        }

    def metrics(self):
        def start_response(status, headers):
            response.status = int(status.split(" ")[0])
            for k, v in headers:
                response.set_header(k, v)
        return prometheus_app(request.environ, start_response)

    def list_plugs(self):
        return {
            "plugs": list(map(plug_to_dict, self.plugs.values())),
        }

    def get_plug(self, uuid):
        plug = self.plugs.get(uuid)
        if plug is None:
            abort(404)
        return plug_to_dict(plug)

    def turn_off_plug(self, uuid):
        plug = self.plugs.get(uuid)
        if plug is None:
            abort(404)
        plug.turn_off()

    def turn_on_plug(self, uuid):
        plug = self.plugs.get(uuid)
        if plug is None:
            abort(404)
        plug.turn_on()


def make_bottle_app(meross_manager):
    return MerossProxyApp(meross_manager=meross_manager).app


manager = MerossManager.from_email_and_password(
    meross_email=EMAIL, meross_password=PASSWORD,
)
make_bottle_app(meross_manager=manager).run(host=HOST, port=PORT)
