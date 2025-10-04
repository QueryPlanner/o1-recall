from mangum import Mangum
from app.main import app

# Mangum adapter converts ASGI (FastAPI) to AWS Lambda/Vercel handler format
# lifespan="off" because we handle lifespan in the app itself
handler = Mangum(app, lifespan="off")

