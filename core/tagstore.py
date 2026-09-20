# region(python_imports)

import json
from pathlib import Path

# endregion

# region(project_imports)

# There is nothing here

# endregion

# region(globals)

# There is nothing here

# endregion

class TagStore:
    """Persistent store for Filmroll's global tag vocabulary."""

# region(class_methods)

    def __init__(self, path: Path):
        self._path = Path(path)
        self._tags = set()

        self._load()

# endregion

# region(methods)

    def get(self) -> list[str]:
        """Return all known tags."""
        return sorted(self._tags)

    def add(self, tag: str) -> bool:
        """
        Add a tag to the global vocabulary.

        Returns True if the tag was added,
        False if it already existed or was invalid.
        """

        if not isinstance(tag, str):
            return False

        tag = tag.strip().lower()
        if not tag or tag in self._tags:
            return False

        self._tags.add(tag)
        return True

    def save(self) -> None:
        """Save the current tag vocabulary to disk."""

        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {"tags": self.get()}
        with self._path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False,)

# endregion

# region(private_methods)

    def _load(self) -> None:
        """Load the tag vocabulary from disk."""

        if not self._path.exists():
            return

        try:
            with self._path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            tags = data.get("tags", [])
            self._tags = {
                tag.strip().lower()
                for tag in tags
                if isinstance(tag, str) and tag.strip()
            }

        except (OSError, json.JSONDecodeError):
            self._tags = set()

# endregion

