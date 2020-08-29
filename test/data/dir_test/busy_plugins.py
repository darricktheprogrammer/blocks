# pollute the namespace with classes to make sure that only classes defined in
# this module are loaded as plugins
from collections import *
from blocks.base import IPlugin


class BusyPlugin1(IPlugin):
	pass


class BusyPlugin2(IPlugin):
	pass


class HelperClass:
	"""A non-plugin class for ensuring that only descendants of IPlugin are loaded as plugins"""

	pass
