from addondev import initializer
import os

# Initialize mock kodi environment
source_dir = os.path.dirname(os.path.dirname(__file__))
addon_dir = os.path.basename(source_dir)
initializer(os.path.join(source_dir, addon_dir))
