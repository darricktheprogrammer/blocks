"""Base class which libraries should inherit from."""


class IPlugin:
	categories = []

	def __init__(self):
		self.enabled = True

	def enable(self):
		self.enabled = True

	def disable(self):
		self.enabled = False
