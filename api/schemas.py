"""Pydantic schemas for the demand forecasting API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    product_id: int = Field(..., description="Product identifier")
    date: str = Field(..., description="Feature date YYYY-MM-DD (predicts next day)")


class PredictResponse(BaseModel):
    product_id: int
    date: str
    predicted_purchases_next_day: float
    actual_purchases_next_day: float | None = Field(
        None,
        description="Ground-truth next-day purchases from gold (null if unavailable)",
    )
    prediction_error: float | None = Field(
        None,
        description="predicted - actual (null if actual unavailable)",
    )
    model_used: str
    features_used: dict
    note: str | None = None


class TopProductItem(BaseModel):
    rank: int
    product_id: int
    predicted_purchases_next_day: float
    actual_purchases_next_day: float | None = None
    prediction_error: float | None = None
    purchases: float | None = None
    views: float | None = None


class TopProductsResponse(BaseModel):
    date: str
    limit: int
    model_used: str
    count: int
    products: list[TopProductItem]
    note: str | None = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: str
    gold_data_range: dict
