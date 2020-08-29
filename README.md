Blocks
======

Build an application one block at a time.

A dead simple plugin manager for Python. No sidecar manifests. No entry_points. Simply Inherit from `blocks.IPlugin`, point the `blocks.PluginManager` at a directory, file or Module and your plugins are loaded.


Example usage for a drawing application:

```python
from blocks import PluginManager
from mymodule.plugins import builtin, contrib

# Load from a module (useful for builtin/core plugins)
plugins = PluginManager()
plugins.load_from_module(builtin, as_category='builtin')
plugins.load_from_module(contrib, as_category='community')

# Load user's personal/installed plugins
user_plugins = plugins.load_from_path(['/path/to/user/plugins'])
plugins.apply_category('user', to=user_plugins)

# Disable all community plugins
for p in plugins.filter_by_category('community'):
	p.disable()

# Get one or more brushes
brushes = plugins.filter_by_category('brush')
round_brush = plugins.get_by_name('roundbrush')

# Get all brushes filtered by two categories. This can be provided as a list
# or a dot separated string.
community_brushes = plugins.filter_by_category('community.brush', include_disabled=True)
builtin_brushes = plugins.filter_by_category(['builtin', 'brush'])

# Disable and re-enable a plugin
plugins.get_by_name('roundbrush').disable()
plugins.get_by_name('roundbrush', include_disabled=True).enable()
```

See more detailed information in the Docs (Not completed yet)
