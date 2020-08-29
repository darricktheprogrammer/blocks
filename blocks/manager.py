import importlib
import inspect
from pathlib import Path
from itertools import chain

import attr

from blocks.base import IPlugin


@attr.s
class PluginManager:
	"""
	Manage the loading, storing and querying of all plugins.

	The `PluginManager` is the main entry point into Blocks. It provides
	several methods for loading plugins and retrieving them back. You are able
	to get all plugins available, filter by category, or select single plugins
	by name. The only prerequisite for loading a plugin is that it is a class
	that inherits from `IPlugin` and it resides in an importable module.

	`PluginManager` does not guarantee an order that plugins will be returned.
	"""

	_plugins = attr.ib(init=False, default=attr.Factory(list))
	_plugins_by_name = attr.ib(init=False, default=attr.Factory(dict))
	_plugins_by_category = attr.ib(init=False, default=attr.Factory(dict))

	def _save_plugin(self, plugin_name, plugin):
		self._plugins.append(plugin)
		self._plugins_by_name[plugin_name] = plugin
		for category in self._collect_inherited_categories(plugin):
			self.apply_categories(category, plugin)

	def _collect_inherited_categories(self, plugin):
		inherited_categories = []
		ancestors = inspect.getmro(plugin.__class__)
		for plugin_class in ancestors:
			if plugin_class == IPlugin:
				break
			unique_categories = [
				c
				for c in plugin_class.categories
				if c not in inherited_categories
			]
			inherited_categories.extend(unique_categories)
		return inherited_categories

	def apply_categories(self, categories, to=None):
		"""
		Apply categories to a plugin at runtime.

		In addition to defining categories as part of a plugin class,
		categories can be defined at runtime by calling `apply_categories` on
		a plugin. This allows plugins loaded from one module to belong to one
		category, but another module to belong to another, even if they have
		the same base class.

		As a convenience, `apply_categories` also accepts a single String for
		categories, if only one category should be applied.

		Args:
			categories (List,String): A list of categories. Category names
				cannot contain periods, but otherwise accept any character.

				As a convenience, `apply_categories` also accepts a single
				String for categories, if only one category should be applied.
		Kwargs:
			to (IPlugin): The plugin in which to apply the category. The `to=`
				can be omitted and the plugin supplied positionally, but it is
				mandatory. The `to` keyword arg is simply supplied for
				api clarity.
		Returns:
			None
		Raises:
			TypeError: In the case that no plugin is supplied either
				positionally or using the keyword argument `to`.
		"""
		if to:
			plugin = to
		else:
			raise TypeError("missing required argument: 'to'")
		if isinstance(categories, str):
			categories = [categories]
		for c in categories:
			if not self._plugins_by_category.get(c, False):
				self._plugins_by_category[c] = []
			self._plugins_by_category[c].append(plugin)

	def all(self, include_disabled=False):
		"""
		Get all of the plugins that have been loaded.

		Kwargs:
			include_disabled (Bool): If True, return the plugin even if its
				`enabled` status is False. Default `False`
		Returns:
			List

			A list of all enabled plugins. This list can be empty if no plugins
			have been loaded
		"""
		return [
			plugin
			for plugin in self._plugins
			if plugin.enabled or include_disabled
		]

	def categories(self):
		return self._plugins_by_category.keys()

	def load_from_module(self, module, as_categories=None):
		"""
		Load plugins located within the given module.

		When loading, only classes who have `IPlugin` somewhere in their
		inheritance heirarchy will be loaded as a plugin. Any helper classes or
		functions will be ignored by Blocks.

		Args:
			module (module): An already imported python module.
		Kwargs:
			as_categories (List,String): Apply categories to all plugins found
				in the module at load time. `as_categories` can be a single
				String, or a list of Strings. See `apply_categories` for
				more information.

				`as_categories` is basically a shortcut for:

					plugins = plugin_manager.load_from_module(module)
					for plugin in plugins:
						plugin_manager.apply_categories(category_name, plugins)
		Returns:
			List

			A list of plugins as defined by the description above.
		"""
		if not as_categories:
			as_categories = []
		loaded_plugins = []
		for name, obj in inspect.getmembers(module):
			# https://stackoverflow.com/a/22578562/2348587
			# Only get classes that are defined inside the loaded module.
			# Imported classes show up in `getmembers` too, but we don't want
			# to load them.
			is_concrete_plugin = (
				inspect.isclass(obj)
				and obj.__module__ == module.__name__
				and IPlugin in inspect.getmro(obj)
			)
			if is_concrete_plugin:
				plugin = obj()
				loaded_plugins.append(plugin)
				self._save_plugin(name, plugin)
				self.apply_categories(as_categories, plugin)
		return loaded_plugins

	def _load_from_file(self, fp, as_categories=None):
		module_name = "blocks.loaded_plugins"
		spec = importlib.util.spec_from_file_location(module_name, fp)
		mod = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(mod)
		return self.load_from_module(mod, as_categories)

	def _load_directory(self, dirpath, recursive=False, as_categories=None):
		module_pattern = "**/*.py" if recursive else "*.py"
		loaded = []
		for filepath in dirpath.glob(module_pattern):
			loaded.extend(
				self._load_from_file(filepath, as_categories=as_categories)
			)
		return loaded

	def load_from_path(self, fp, recursive=False, as_categories=None):
		"""
		Load plugins from a file or directory.

		Due to Python's import rules, any plugin files must be a valid python
		module (i.e. ending with `.py`, `.pyc`, etc.). See
		`PluginLoader.load_plugins_from_module` for more details on how plugins
		are loaded.

		If `fp` is a directory, Blocks will _non-recursively_ search all `.py`
		files within the directory for plugins.

		Args:
			fp (String): The absolute path to a file or directory
		Kwargs:
			recursive (Bool): Whether or not a directory should be searched
				recursively. If `fp` is a file, this option is ignored.
				Default is `False`
			as_categories (List,String): Apply categories to all plugins found
				in the module at load time. `as_categories` can be a single
				String, or a list of Strings. See `apply_categories` for
				more information.

				`as_categories` is basically a shortcut for:

					plugins = plugin_manager.load_from_module(module)
					for plugin in plugins:
						plugin_manager.apply_categories(category_name, plugins)
		Returns:
			List

			A list of plugins as defined by `load_from_module`
		"""
		fp = Path(fp)
		if fp.is_dir():
			return self._load_directory(
				fp, recursive=recursive, as_categories=as_categories
			)
		elif fp.exists():
			return self._load_from_file(fp, as_categories=as_categories)
		else:
			raise FileNotFoundError(f"Error loading plugins from: '{fp}'")

	def filter_by_categories(self, categories, include_disabled=False):
		"""
		Retrieve only plugins that are defined as one of the given categories.

		Categories are defined by the `categories` attribute on the plugin or
		any of its superclasses.

		Args:
			categories (String,Iterable): The categories to filter by. Plugins
				will be filtered against _all_ of the items of the list, which
				act as an `and` clause. For convience, a `String` can be passed
				as the `categories` argument to filter by a single category.

				`filter_by_categories` also accepts a dot separated notation for
				multiple categories, meaning `['text_filter', 'markdown']` is
				equivalent to `'text_filter.markdown'`.

				!!! warning: This means that a category cannot contain a period
				as part of its name. Any other character will work fine.
			include_disabled (Bool): If True, return the plugin even if its
				`enabled` status is False. Default `False`
		Returns:
			List

			A list of plugins matching the given categories. If none of the
			categories have been previously defined, an empty list will
			be returned.
		"""
		if isinstance(categories, str):
			categories = [categories]
		# flatten an arbitrary length list of dot-separated categories
		categories = chain.from_iterable([c.split(".") for c in categories])
		matched = [
			plugin
			for plugin in (
				self._plugins_by_category.get(c, []) for c in categories
			)
			if plugin
		]
		try:
			first, *rest = matched
			unique_list = set(first).intersection(*rest)
			return [
				plugin
				for plugin in unique_list
				if plugin.enabled or include_disabled
			]
		except ValueError:
			# not enough values to unpack (`matched` is an empty list)
			return []

	def get_by_name(self, plugin_name, include_disabled=False):
		"""
		Retrieve a single plugin.

		Args:
			plugin_name (String): The name of the plugin. This is its class
				name. While a library can define a `name` attribute for
				a plugin, Blocks simply stores plugins by their class name.
			include_disabled (Bool): If True, return the plugin even if its
				`enabled` status is False. Default `False`
		Returns:
			IPlugin
		Raises:
			NameError: In the case of no plugin being found by that name.
			AtrributeError: In the case that the plugin is found, but disabled
				and `include_disabled` is False.
		"""
		try:
			plugin = self._plugins_by_name[plugin_name]
		except KeyError:
			raise NameError(f"No plugins loaded named '{plugin_name}'")
		should_return = plugin.enabled or include_disabled
		if not should_return:
			raise AttributeError(f"Plugin '{plugin_name}' is disabled")
		return plugin
