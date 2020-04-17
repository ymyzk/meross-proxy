import os

from bottle import abort, route, run
from meross_iot.cloud.devices.power_plugs import GenericPlug
from meross_iot.manager import MerossManager


HOST = os.environ.get("PROXY_HOST", "localhost")
PORT = int(os.environ.get("PROXY_PORT", "8080"))
EMAIL = os.environ.get('MEROSS_EMAIL')
PASSWORD = os.environ.get('MEROSS_PASSWORD')


def plug_to_dict(p):
    return {
        "uuid": p.uuid,
        "name": p.name,
        "online": p.online,
        "fwversion": p.fwversion,
        "status": p.get_status(),
    }


@route('/plugs')
def list_plugs():
    return {
        "plugs": list(map(plug_to_dict, plugs.values())),
    }


@route('/plugs/<uuid:re:[0-9a-f]+>')
def get_plug(uuid):
    plug = plugs.get(uuid)
    if plug is None:
        abort(404)
    return plug_to_dict(plug)


@route('/plugs/<uuid:re:[0-9a-f]+>/turn_off', method='POST')
def turn_off_plug(uuid):
    plug = plugs.get(uuid)
    if plug is None:
        abort(404)
    plug.turn_off()


@route('/plugs/<uuid:re:[0-9a-f]+>/turn_on', method='POST')
def turn_on_plug(uuid):
    plug = plugs.get(uuid)
    if plug is None:
        abort(404)
    plug.turn_on()


manager = MerossManager.from_email_and_password(
        meross_email=EMAIL,
        meross_password=PASSWORD,
)
manager.start()
plugs = {d.uuid: d for d in manager.get_devices_by_kind(GenericPlug)}
run(host=HOST, port=PORT)
