from database.database_manager import DatabaseManager
from .experiments import ExperimentsPage


class DatabasePage(ExperimentsPage):
    def __init__(self, parent, db_manager: DatabaseManager | None = None) -> None:
        super().__init__(parent, db_manager=db_manager, start_tab="database")
