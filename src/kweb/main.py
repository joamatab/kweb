import base64
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, Request
from starlette.endpoints import WebSocketEndpoint
from starlette.routing import WebSocketRoute
from starlette.requests import Request as StRequest
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import status

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


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    active_pdk = gf.get_active_pdk()
    pdk_name = active_pdk.name
    components = list(active_pdk.cells.keys())
    return templates.TemplateResponse('index.html', {'request': request, 'title': 'Main', 'pdk_name': pdk_name, 'components': components})


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
LOADED_COMPONENTS = {}
@app.get("/view/{cell_name}", response_class=HTMLResponse)
async def view_cell(request: Request, cell_name: str, variant: Optional[str] = None):
    if variant in LOADED_COMPONENTS:
        component = LOADED_COMPONENTS[variant]
    else:
        component = gf.get_component(cell_name)
    layout_view = get_layout_view(component)
    pixel_data = layout_view.get_pixels_with_options(1000, 800).to_png_data()
    # pixel_data = layout_view.get_screenshot_pixels().to_png_data()
    b64_data = base64.b64encode(pixel_data).decode("utf-8")
    return templates.TemplateResponse(
        "viewer.html",
        {
            "request": request,
            "cell_name": str(cell_name),
            "variant": variant,
            "title": "Viewer",
            "initial_view": b64_data,
            "component": component,
        },
    )


@app.post("/update/{cell_name}")
async def update_cell(request: Request, cell_name: str):
    data = await request.form()
    changed_settings = {k: float(v) for k, v in data.items() if v != ''}
    new_component = gf.get_component({'component': cell_name, 'settings': changed_settings})
    LOADED_COMPONENTS[new_component.name] = new_component
    logger.info(data)
    return RedirectResponse(f"/view/{cell_name}?variant={new_component.name}",  status_code=status.HTTP_302_FOUND)

@app.post("/search", response_class=RedirectResponse)
async def search(name: str = Form(...)):
    logger.info(f'Searching for {name}...')
    try:
        gf.get_component(name)
    except ValueError:
        return RedirectResponse("/", status_code=status.HTTP_404_NOT_FOUND)
    logger.info(f'Successfully found {name}! Redirecting...')
    return RedirectResponse(f"/view/{name}", status_code=status.HTTP_302_FOUND)
