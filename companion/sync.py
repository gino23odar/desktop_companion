"""Single-owner synchronization loop; server polling and USB recovery are independent."""
import logging
import time

from .connection import connect
from .protocol import DeviceError, LinkError, ProtocolError
from .remote import RemoteClient, RemoteError
from .sync_cache import MoodCache
from .sync_models import normalize_mood

LOG = logging.getLogger(__name__)
POLL_INTERVAL = 5.0
RECONCILE_INTERVAL = 15.0
USB_RETRY = 2.0
HEARTBEAT = 3.0
MAX_HTTP_RETRY = 60.0


class Synchronizer:
    def __init__(self, remote, cache, *, connector=connect, clock=time.monotonic,
                 sleep=time.sleep, on_event=None, explicit=None, usb_serial=None):
        self.remote, self.cache, self.connector = remote, cache, connector
        self.clock, self.sleep = clock, sleep
        self.on_event = on_event or (lambda event: None)
        self.explicit, self.usb_serial = explicit, usb_serial
        self.desired = cache.load()
        self.cached = self.desired
        self.client = None
        self.next_http = self.next_usb = self.next_check = self.next_ping = clock()
        self.http_delay = POLL_INTERVAL
        self.dirty = True

    def event(self, event):
        if event.get("type") == "ready":
            self.dirty = True
        self.on_event(event)

    def _fetch(self):
        try:
            publication = self.remote.fetch()
        except RemoteError as exc:
            LOG.warning("Remote unavailable: %s; retaining last valid state", exc)
            self.next_http = self.clock() + self.http_delay
            self.http_delay = min(self.http_delay * 2, MAX_HTTP_RETRY)
            return
        self.http_delay = POLL_INTERVAL
        self.next_http = self.clock() + POLL_INTERVAL
        if self.desired != publication:
            if self.desired and publication["revision"] < self.desired["revision"]:
                LOG.warning("Server revision decreased; accepting current authoritative snapshot")
            self.desired = publication
            self.dirty = True
            LOG.info("Received published revision %s", publication["revision"])
        if self.cached != publication:
            try:
                self.cache.save(publication)
                self.cached = publication
            except OSError:
                LOG.warning("Could not save sync cache; continuing in memory")

    def _read_mood(self):
        reply = self.client.request("get_mood")
        try:
            return normalize_mood(reply.get("mood"))
        except ValueError:
            raise ProtocolError("Device returned an invalid mood") from None

    def _reconcile(self):
        if self.desired is not None:
            wanted = self.desired["mood"]
            if self._read_mood() != wanted:
                # A timeout is ambiguous. Reconnect and read back before any retry.
                self.client.request("set_mood", mood=wanted)
                if self._read_mood() != wanted:
                    raise ProtocolError("Device readback differs from published mood")
                LOG.info("Applied and verified revision %s", self.desired["revision"])
            else:
                LOG.debug("Device already matches revision %s", self.desired["revision"])
        self.dirty = False
        self.next_check = self.clock() + RECONCILE_INTERVAL
        self.next_ping = self.clock() + HEARTBEAT

    def close(self):
        client, self.client = self.client, None
        if client is not None:
            try:
                client.close()
            except OSError:
                LOG.warning("Could not close USB port cleanly")

    def step(self):
        if self.clock() >= self.next_http:
            self._fetch()
        if self.client is None and self.clock() < self.next_usb:
            return
        try:
            if self.client is None:
                self.client = self.connector(explicit=self.explicit, usb_serial=self.usb_serial, on_event=self.event)
                self.dirty = True
                self.next_ping = self.clock() + HEARTBEAT
            self.client.poll(timeout=0.1)
            if self.dirty or self.clock() >= self.next_check:
                # If there is no desired state, leave the physical mood untouched.
                if self.desired is not None:
                    self._reconcile()
                else:
                    self.dirty = False
                    self.next_check = self.clock() + RECONCILE_INTERVAL
            if self.clock() >= self.next_ping:
                self.client.request("ping")
                self.next_ping = self.clock() + HEARTBEAT
        except (LinkError, DeviceError, OSError) as exc:
            LOG.warning("USB unavailable (%s); retrying after readback on reconnect", type(exc).__name__)
            self.close()
            self.dirty = True
            self.next_usb = self.clock() + USB_RETRY

    def run(self, should_stop=lambda: False):
        try:
            while not should_stop():
                self.step()
                self.sleep(0.15)
        finally:
            self.close()


def run_sync(settings, **options):
    Synchronizer(RemoteClient(settings), MoodCache(settings.cache_path, settings.url), **options).run()
