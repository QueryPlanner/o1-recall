from mangum import Mangum
import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

handler = Mangum(app, lifespan="off")

