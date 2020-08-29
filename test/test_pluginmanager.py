#!/usr/bin/env python3
import os
import inspect

import pytest

from blocks import PluginManager
from blocks.base import IPlugin
from test.data import bare_plugins
from test.data import busy_plugins
from test.data import no_plugins
from test.data import inherited_plugins

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(TEST_DIR, 'data')


@pytest.mark.integration
def test_PluginManager_WhenLoadingModule_InitializesPluginObject():
	"""
	This should be really obvious, and not an issue. But that wasn't the case
	early on, and I was having a lot of weird subtle errors because it
	turned out that I wasn't instantiating the plugins, so everything I was
	working with was a class instead of an instance.

	Now that it's fixed, I doubt it will regress to be a problem again, but
	better safe than sorry.
	"""
	plugins = PluginManager()
	plugins.load_from_module(bare_plugins)
	plugin = plugins.all()[0]
	assert not inspect.isclass(plugin)


@pytest.mark.integration
class TestImports:
	def setup_method(self):
		self.plugins = PluginManager()

	def _assert_all_are_plugins(self, plugin_list):
		for plugin in plugin_list:
			assert IPlugin in inspect.getmro(plugin.__class__)

	def test_LoadFromModule_GivenModule_LoadsPlugins(self):
		self.plugins.load_from_module(bare_plugins)
		loaded = self.plugins.all()
		assert len(loaded) == 2
		self._assert_all_are_plugins(loaded)

	def test_LoadFromModule_GivenBusyModule_OnlyLoadsIPluginDescendants(self):
		"""
		Ensure that only plugins are loaded.

		When a module is imported, all imports, classes, and functions are
		available. Make sure that only classes that are defined within the
		module itself and are descended from `IPlugin` are loaded.
		"""
		self.plugins.load_from_module(busy_plugins)
		loaded = self.plugins.all()
		assert len(loaded) == 2
		self._assert_all_are_plugins(loaded)

	def test_LoadFromModule_GivenEmptyModule_ReturnsEmptyList(self):
		self.plugins.load_from_module(no_plugins)
		loaded = self.plugins.all()
		assert len(loaded) == 0


	def test_LoadFromPath_GivenFilePath_LoadsPlugins(self):
		self.plugins.load_from_path(os.path.join(DATA_DIR, 'bare_plugins.py'))
		loaded = self.plugins.all()
		assert len(loaded) == 2

	def test_LoadFromPath_GivenDirectoryPath_LoadsAllPluginsInDirectory(self):
		self.plugins.load_from_path(os.path.join(DATA_DIR, 'dir_test'))
		loaded = self.plugins.all()
		assert len(loaded) == 4

	def test_LoadFromPath_GivenNonExistentPath_ThrowsError(self):
		with pytest.raises(FileNotFoundError):
			self.plugins.load_from_path(os.path.join(DATA_DIR, 'no_exist'))

	def test_LoadFromPath_DirectoryWithRecursiveTrue_LoadsAllPluginsInDirectory(self):
		test_dir = os.path.join(DATA_DIR, 'dir_test')
		self.plugins.load_from_path(test_dir, recursive=True)
		loaded = self.plugins.all()
		assert len(loaded) == 6

	def test_LoadFromPath_FileWithRecursiveTrue_IgnoresRecursiveFlag(self):
		test_path = os.path.join(DATA_DIR, 'bare_plugins.py')
		self.plugins.load_from_path(test_path, recursive=True)
		loaded = self.plugins.all()
		assert len(loaded) == 2


@pytest.mark.integration
class TestFiltering:
	def setup_method(self):
		self.plugins = PluginManager()

	def test_GetAll_AllDisabled_ReturnsEmptyList(self):
		self.plugins.load_from_module(bare_plugins)
		assert len(self.plugins.all()) > 0
		for plugin in self.plugins.all():
			plugin.disable()
		assert len(self.plugins.all()) == 0

	def test_GetAll_AllDisabledIncludeDisabledTrue_ReturnsAllPlugins(self):
		self.plugins.load_from_module(bare_plugins)
		all_count = len(self.plugins.all())
		for plugin in self.plugins.all():
			plugin.disable()
		assert len(self.plugins.all(include_disabled=True)) == all_count

	def test_FilterByCategories_CategoryDefinedInPlugin_ReturnsFilteredPlugins(self):
		self.plugins.load_from_module(inherited_plugins)
		text_filters = self.plugins.filter_by_categories('markdown')
		assert len(text_filters) == 2

	def test_FilterByCategories_CategoryDefinedInSuperClass_ReturnsAllSubclassPlugins(self):
		self.plugins.load_from_module(inherited_plugins)
		text_filters = self.plugins.filter_by_categories('text_filter')
		assert len(text_filters) == 3

	def test_FilterByCategories_CategoryDoesntExist_ReturnsEmptyList(self):
		self.plugins.load_from_module(inherited_plugins)
		text_filters = self.plugins.filter_by_categories('non-existent category')
		assert len(text_filters) == 0

	def test_FilterByCategories_GivenMultipleCategories_ReturnsFilteredPlugins(self):
		self.plugins.load_from_module(inherited_plugins)
		text_filters = self.plugins.filter_by_categories(['file_locator', 'markdown'])
		assert len(text_filters) == 1

	def test_FilterByCategories_OneCategoryExistsButOneDoesnt_ReturnsFilteredByExisting(self):
		self.plugins.load_from_module(inherited_plugins)
		text_filters = self.plugins.filter_by_categories(['non-existent category', 'markdown'])
		assert len(text_filters) == 2

	def test_FilterByCategories_GivenSingleDotSeparatedCategories_ReturnsFiltered(self):
		self.plugins.load_from_module(inherited_plugins)
		text_filters = self.plugins.filter_by_categories('text_filter.markdown')
		assert len(text_filters) == 1

	def test_FilterByCategories_GivenDotSeparatedCategoriesInList_ReturnsFiltered(self):
		self.plugins.load_from_module(inherited_plugins)
		text_filters = self.plugins.filter_by_categories(['text_filter.markdown', 'non-existent category'])
		assert len(text_filters) == 1

	def test_FilterByCategories_PluginsAreDisabled_ReturnsEmptyList(self):
		self.plugins.load_from_module(inherited_plugins)
		for plugin in self.plugins.all():
			plugin.disable()
		text_filters = self.plugins.filter_by_categories('text_filter')
		assert len(text_filters) == 0

	def test_FilterByCategories_PluginsAreDisabledButIncludeDisabledIsTrue_ReturnsEmptyList(self):
		self.plugins.load_from_module(inherited_plugins)
		for plugin in self.plugins.all():
			plugin.disable()
		text_filters = self.plugins.filter_by_categories('text_filter', include_disabled=True)
		assert len(text_filters) == 3


	def test_GetPluginByName_GivenName_ReturnsPlugin(self):
		self.plugins.load_from_module(bare_plugins)
		plugin = self.plugins.get_by_name('BarePlugin1')
		assert isinstance(plugin, bare_plugins.BarePlugin1)

	def test_GetPluginByName_NameDoesntExist_ThrowsError(self):
		self.plugins.load_from_module(bare_plugins)
		with pytest.raises(NameError):
			plugin = self.plugins.get_by_name('BarePluginX')

	def test_GetPluginByName_PluginDisabled_ThrowsError(self):
		self.plugins.load_from_module(bare_plugins)
		for plugin in self.plugins.all():
			plugin.disable()
		with pytest.raises(AttributeError):
			plugin = self.plugins.get_by_name('BarePlugin1')

	def test_GetPluginByName_PluginDisabledButIncludeDisabled_ReturnsPlugin(self):
		self.plugins.load_from_module(bare_plugins)
		for plugin in self.plugins.all():
			plugin.disable()
		plugin = self.plugins.get_by_name('BarePlugin1', include_disabled=True)
		assert isinstance(plugin, bare_plugins.BarePlugin1)


@pytest.mark.integration
class TestCategories:
	def setup_method(self):
		self.plugins = PluginManager()

	def test_GetCategories_NoCategories_ReturnsEmptyList(self):
		categories = self.plugins.categories()
		assert len(categories) == 0

	def test_GetCategories_CategoryDefinedAtLoad_ReturnsCategories(self):
		self.plugins.load_from_module(bare_plugins, as_categories='bare')
		categories = self.plugins.categories()
		assert len(categories) == 1

	def test_GetCategories_CategoriesDefinedInClass_ReturnsCategories(self):
		self.plugins.load_from_module(inherited_plugins)
		categories = self.plugins.categories()
		assert len(categories) == 3

	def test_ApplyCategory_ArbitraryCategory_AppliesCategoryToPlugin(self):
		self.plugins.load_from_module(bare_plugins)
		plugin = self.plugins.all()[0]
		self.plugins.apply_categories('category_name', plugin)
		assert len(self.plugins.filter_by_categories('category_name')) == 1

	def test_ApplyCategory_UsingToKwarg_AppliesCategoryToPlugin(self):
		self.plugins.load_from_module(bare_plugins)
		plugin = self.plugins.all()[0]
		self.plugins.apply_categories('category_name', to=plugin)
		assert len(self.plugins.filter_by_categories('category_name')) == 1

	def test_ApplyCategory_CalledWithOnlyPositionalArguments_AppliesCategoryToPlugin(self):
		self.plugins.load_from_module(bare_plugins)
		plugin = self.plugins.all()[0]
		self.plugins.apply_categories('category_name', plugin)
		assert len(self.plugins.filter_by_categories('category_name')) == 1

	def test_ApplyCategory_GivingNoPlugin_ThrowsError(self):
		self.plugins.load_from_module(bare_plugins)
		with pytest.raises(TypeError):
			self.plugins.apply_categories('category_name')

	def test_LoadFromModule_ApplyingSingleCategoryToSingleModule_AppliesCategory(self):
		self.plugins.load_from_module(bare_plugins, as_categories='no-inheritance')
		self.plugins.load_from_module(inherited_plugins)
		plugins = self.plugins.filter_by_categories('no-inheritance')
		assert len(plugins) == 2

	def test_LoadFromModule_ApplyingListOfCategoriesToSingleModule_AppliesCategories(self):
		self.plugins.load_from_module(bare_plugins, as_categories=['no-inheritance', 'versatile'])
		self.plugins.load_from_module(inherited_plugins)
		non_inheritance_plugins = self.plugins.filter_by_categories('no-inheritance')
		versatile_plugins = self.plugins.filter_by_categories('versatile')
		assert len(non_inheritance_plugins) == 2
		assert non_inheritance_plugins == versatile_plugins

	def test_LoadFromPath_ApplyingSingleCategoryToSingleModule_AppliesCategory(self):
		self.plugins.load_from_path(
			os.path.join(DATA_DIR, 'bare_plugins.py'),
			as_categories='no-inheritance')
		self.plugins.load_from_path(os.path.join(DATA_DIR, 'inherited_plugins.py'))
		plugins = self.plugins.filter_by_categories('no-inheritance')
		assert len(plugins) == 2

	def test_LoadFromPath_ApplyingListOfCategoriesToSingleModule_AppliesCategory(self):
		bare_path = os.path.join(DATA_DIR, 'bare_plugins.py')
		inherited_path = os.path.join(DATA_DIR, 'inherited_plugins.py')
		self.plugins.load_from_path(bare_path, as_categories=['no-inheritance', 'versatile'])
		self.plugins.load_from_path(inherited_path)
		plugins = self.plugins.filter_by_categories('no-inheritance')
