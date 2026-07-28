"""FastAPI demo: next-day purchase demand forecasts from gold features."""
from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from api.predictor import DemandPredictor
from api.schemas import (
    HealthResponse,
    PredictRequest,
    PredictResponse,
    TopProductsResponse,
)

_predictor: DemandPredictor | None = None


def get_predictor() -> DemandPredictor:
    global _predictor
    if _predictor is None:
        _predictor = DemandPredictor()
    return _predictor


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_predictor()
    except FileNotFoundError as exc:
        print(f"API warning: {exc}")
    yield


app = FastAPI(
    title="Demand Forecasting API",
    description=(
        "Predicts next-day purchase count for a product given its "
        "clickstream-derived features on a calendar date (demo)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        pred = get_predictor()
        return HealthResponse(
            status="ok",
            model_loaded=pred.model_name,
            gold_data_range=pred.get_gold_date_range(),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    try:
        pred = get_predictor()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    result = pred.predict(request.product_id, request.date)
    return PredictResponse(**result)


@app.get("/products")
def list_products(limit: int = 20) -> list[dict]:
    try:
        pred = get_predictor()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return pred.top_products(limit=limit)


@app.get("/top", response_model=TopProductsResponse)
def top_predicted(
    date: str,
    limit: int = 10,
    min_views: float = 0.0,
) -> TopProductsResponse:
    """Top-N products by predicted next-day purchases for a gold feature date."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    try:
        pred = get_predictor()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    result = pred.top_predicted(date=date, limit=limit, min_views=min_views)
    if result["count"] == 0 and result.get("note"):
        raise HTTPException(status_code=404, detail=result["note"])
    return TopProductsResponse(**result)
