"""Model format-based templating."""


class Formatter(object):
    """
    Thin veneer over a dictionary and string formatting using its values.

    :Args:
        **kwargs
            (optional) Keyword arguments to initialize keys/values for
            formatting.
    """

    def __init__(self, **kwargs):
        self.dict = dict(kwargs)

    def add(self, **kwargs):
        """Add `kwargs` as keys/values for formatting."""
        self.dict.update(kwargs)

    def set(self, key, value):
        """Add a key/value for formatting."""
        self.dict[key] = value

    def get(self, key, default=None, should_raise=False):
        """Retrieve the value for a key."""
        if should_raise:
            return self.dict[key]
        return self.dict.get(key, default)

    def has(self, key):
        """Tell whether we have `key`."""
        return key in self.dict

    def keys(self):
        """Retrieve the list of formatting keys."""
        return list(self.dict.keys())

    def format(self, template):
        """
        Format `template` using key/value pairs and string formatting.

        :Args:
            template
                Either a string or an iterable.  If a string, it is formatted
                directly.  If another kind of iterable, each element is
                formatted individually.

        :Returns:
            Either a string or a list, depending on `template`.
        """
        if isinstance(template, str):
            return template.format(**self.dict)
        return [x.format(**self.dict) for x in template]
