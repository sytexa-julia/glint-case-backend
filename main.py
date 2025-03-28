import os
from contextlib import asynccontextmanager

import xarray as xr
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

class WaveHeight(BaseModel):
    # req_latlng: Optional[Tuple[float,float]]
    # act_latlng: Optional[Tuple[float,float]]
    # req_act_dist: Optional[float]
    max_height: float
    max_height_time: str


data = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # In a real app we would probably use a more robust+scalable data storage method
    waves = xr.open_dataset("waves_2019-01-01.nc", engine="netcdf4")
    data["waves"] = waves
    yield
    waves.close()
    data.clear()


app = FastAPI(lifespan=lifespan)

env_allow_origins = (os.getenv("CORS_ORIGINS", "")).split(sep=None, maxsplit=-1)
env_allow_origins.extend([
    "http://localhost",
    "http://localhost:8080",
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=env_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/waves/max_height")
async def max_height(lat: float, lng: float):
    """
    Retrieve the hmax (max. wave height), and the time it was recorded at the given coordinates.
    The returned values will be for the point nearest to the given coordinates that has valid data.
    Coordinates on land return an empty result.

    :param lat: latitude
    :param lng: longitude
    :return: JSONResponse with WaveHeight data, or HTTPException on failure.
    """
    try:
        waves_data = data["waves"]
        waves_at_point = waves_data.hmax.sel(latitude=lat, longitude=lng, method="nearest")

        # If all the data points are null, the coordinates are on (or near) land
        if waves_at_point.isnull().all().item():
            return JSONResponse(content=jsonable_encoder(WaveHeight()))

        # Since we are taking the data at the "nearest" point to the given lat/lng...
        # Something like this could be useful to indicate the ACTUAL lat/lng that the data was
        # collected at:
        #
        # req_latlng = (lat, lng)
        # actual_latlng = (waves_at_point.latitude.item(), waves_at_point.longitude.item())
        # req_act_dist = distance.great_circle(req_latlng, actual_latlng).kilometers

        max_idx = waves_at_point.argmax(dim="time")
        max_hgt = waves_at_point[max_idx].item()
        max_time = waves_at_point.time[max_idx].values.astype("datetime64[s]").astype("str")

        response_obj = WaveHeight(
            max_height=max_hgt,
            max_height_time=max_time
        )

        return JSONResponse(content=jsonable_encoder(response_obj))
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
