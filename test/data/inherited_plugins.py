from blocks.base import IPlugin


class BaseTextFilter(IPlugin):
	# effective categories: ['text_filter']
	categories = ["text_filter"]


class BaseFileLocator(IPlugin):
	# effective categories: ['file_locator']
	categories = ["file_locator"]


class UncategorizedTextFilter(BaseTextFilter):
	# effective categories: ['text_filter']
	pass


class MarkdownTextFilter(BaseTextFilter):
	# effective categories: ['text_filter', 'markdown']
	categories = ["markdown"]


class MarkdownFileLocator(BaseFileLocator):
	# effective categories: ['file_locator', 'markdown']
	categories = ["markdown"]
