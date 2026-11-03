"""Navigator package for AEOForge."""
from aeoforge.navigator.browser import BrowserNavigator, NavigatedPageData
from aeoforge.navigator.trap_detector import detect_navigation_traps
from aeoforge.navigator.route_interceptor import setup_route_interception
from aeoforge.navigator.som_grounding import extract_interactive_marks, build_a11y_tree_representation

__all__ = [
    "BrowserNavigator",
    "NavigatedPageData",
    "detect_navigation_traps",
    "setup_route_interception",
    "extract_interactive_marks",
    "build_a11y_tree_representation"
]
