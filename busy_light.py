import platform
import logging
import threading
import time

is_windows = platform.system() == "Windows"
logger = logging.getLogger("BusyLight")

if is_windows:
	from busylight_core import EmbravaLights # PC version
else:
	import hid # Mac version

class BusyLightDriver:
	def __init__(self):
		self.device = None
		self._blink_thread = None
		self._blinking = False

		if is_windows:
			try:
				self.light = EmbravaLights.all_lights()[0]
			except Exception:
				self.light = None
		else:
			self.light = None

	def _blink_loop(self):
		while self._blinking:
			self.set_color(50, 0, 0)

			for _ in range(5):  # break sleep into chunks
				if not self._blinking:
					return
				time.sleep(0.1)

			self.set_color(0, 0, 0)

			for _ in range(5):
				if not self._blinking:
					return
				time.sleep(0.1)

	# MAC DEVICE
	def _connect(self):
		if self.device:
			return self.device

		for d in hid.enumerate():
			if "blync" in (d.get("product_string") or "").lower():
				self.device = hid.device()
				self.device.open(d["vendor_id"], d["product_id"])
				self.open_path(d["path"])
				return self.device
		return None

	def _set_mac(self, r, g, b):
		try:
			dev = self._connect()
			if not dev:
				return

			report = [0, r, g, b, 0, 0, 0, 0, 0]
			dev.write(report)
		except Exception as ex:
			if self.device:
				try:
					self.device.close()
				except Exception:
					pass

			self.device = None

	# WINDOWS DEVICE
	def _set_win(self, r, g, b):
		if self.light:
			self.light.on((r, g, b))

	# PUBLIC API
	def start_blink(self):
		if self._blinking:
			return
		self._blinking = True
		self._blink_thread = threading.Thread(target=self._blink_loop, daemon=True)
		self._blink_thread.start()

	def stop_blink(self):
		if not self._blinking:
			return

		self._blinking = False

		if self._blink_thread:
			self._blink_thread.join(timeout=1)  # wait for thread to fully stop
			self._blink_thread = None


	def set_status(self, status):
		if status == "fail":
			self.start_blink()
			# self.set_color(50, 0, 0)
		elif status == "ok":
			self.stop_blink()
			# if status == "ok":
			self.set_color(0, 0, 50)

	def set_color(self, r, g, b):
		if is_windows:
			self._set_win(r, b, g)
		else:
			self._set_mac(r, g, b)

	def off(self):
		self.stop_blink()
		self.set_color(0, 0, 0)

	# Safety Shutdown
	def shutdown(self):
		try:
			self.off()
			if self.device:
				self.device.close()
		except Exception:
			pass