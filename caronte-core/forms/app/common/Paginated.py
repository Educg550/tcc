from typing import List, TypeVar, Generic

Type = TypeVar('Type')

class Paginated(Generic[Type]):
    def __init__(self, items: List[Type] = [], count: int = 0, page_index: int = 0, page_size: int = 0) -> None:
        self.page_index = page_index
        self.total_pages = count // page_size
        self.total_count = count
        self.items = items

        self.has_previous_page = self.page_index > 1
        self.has_next_page = self.page_index < self.total_pages

