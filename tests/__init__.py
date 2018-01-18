from addondev import initializer
import os

# Initialize mock kodi environment
initializer(os.path.dirname(os.path.dirname(__file__)))
