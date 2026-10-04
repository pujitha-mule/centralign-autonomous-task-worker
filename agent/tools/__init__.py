from .files import FilesListTool, FilesReadTool
from .internal_api import InternalApiGetTool
from .browser import BrowserOpenTool, BrowserFillAndSubmitTool
from .human import HumanAskTool


def default_tools():
    return [
        FilesListTool(),
        FilesReadTool(),
        BrowserOpenTool(),
        BrowserFillAndSubmitTool(),
        InternalApiGetTool(),
        HumanAskTool(),
    ]