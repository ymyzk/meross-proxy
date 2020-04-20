import atexit

from bottle import abort, Bottle
from meross_iot.cloud.devices.power_plugs import GenericPlug


def _plug_to_dict(p):
    return {
        "uuid": p.uuid,
        "name": p.name,
        "online": p.online,
        "fwversion": p.fwversion,
        "status": p.get_status(),
    }


class MerossProxyApp:
    def __init__(self, *, meross_manager, prometheus_app):
        # Initialize Bottle application
        app = Bottle()
        app.mount("/metrics", prometheus_app)
        app.route("/healthz", callback=self.healthcheck)
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
        self._plugs = {d.uuid: d for d in meross_manager.get_devices_by_kind(GenericPlug)}

    def healthcheck(self):
        return {
            "status": "OK",
        }

    def list_plugs(self):
        return {
            "plugs": list(map(_plug_to_dict, self._plugs.values())),
        }

    def get_plug(self, uuid):
        plug = self._plugs.get(uuid)
        if plug is None:
            abort(404)
        return _plug_to_dict(plug)

    def turn_off_plug(self, uuid):
        plug = self._plugs.get(uuid)
        if plug is None:
            abort(404)
        plug.turn_off()

    def turn_on_plug(self, uuid):
        plug = self._plugs.get(uuid)
        if plug is None:
            abort(404)
        plug.turn_on()


def make_bottle_app(*, meross_manager, prometheus_app):
    return MerossProxyApp(
        meross_manager=meross_manager,
        prometheus_app=prometheus_app,
    ).app
