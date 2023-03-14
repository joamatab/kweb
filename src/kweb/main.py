import base64
from pathlib import Path

from fastapi import FastAPI, Request
from starlette.endpoints import WebSocketEndpoint
from starlette.routing import WebSocketRoute
from starlette.requests import Request as StRequest
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from kweb.server import LayoutViewServerEndpoint, get_layout_view
import gdsfactory as gf
from loguru import logger


module_path = Path(__file__).parent.absolute()
home_path = Path.home() / ".gdsfactory" / "extra"
home_path.mkdir(exist_ok=True, parents=True)

# app = FastAPI(routes=[WebSocketRoute("/view/ws", endpoint=LayoutViewServerEndpoint)])
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# gdsfiles = StaticFiles(directory=home_path)
# app.mount("/gds_files", gdsfiles, name="gds_files")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root():
    return {
        "message": "Welcome to kweb visualizer: \n go to http://127.0.0.1:8000/gds/wg"
    }


# @app.get("/gds", response_class=HTMLResponse)
# async def gds_view(request: Request, gds_file: str, layer_props: str = home_path):
#     return templates.TemplateResponse(
#         "client.html",
#         {
#             "request": request,
#             "url": str(
#                 request.url.scheme
#                 + "://"
#                 + request.url.hostname
#                 + ":"
#                 + str(request.url.port)
#                 + request.url.path,
#             ),
#             "gds_file": gds_file,
#             # "layer_props": layer_props,
#         },
#     )

@app.get("/view/{cell_name}", response_class=HTMLResponse)
async def view_cell(request: Request, cell_name: str):
    component = gf.get_component(cell_name)
    layout_view = get_layout_view(cell_name=cell_name)
    pixel_data = layout_view.get_pixels_with_options(1000, 800).to_png_data()
    # pixel_data = layout_view.get_screenshot_pixels().to_png_data()
    b64_data = base64.b64encode(pixel_data).decode("utf-8")
    return templates.TemplateResponse(
        "viewer.html",
        {
            "request": request,
            "cell_name": str(cell_name),
            "title": "Viewer",
            "initial_view": b64_data,
            "component": component,
        },
    )

