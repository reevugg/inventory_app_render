def compute_costs(purchase_cost_yen: float, weight_kg: float, exchange_rate: float, shipping_per_kg: float):
    purchase_cost_bdt = (purchase_cost_yen or 0.0) * (exchange_rate or 0.0)
    shipping_cost_bdt = (weight_kg or 0.0) * (shipping_per_kg or 0.0)
    landed = purchase_cost_bdt + shipping_cost_bdt
    suggested_ws = landed * 2.5
    suggested_rt = landed * 3.5
    return {
        "purchase_cost_bdt": round(purchase_cost_bdt, 2),
        "shipping_cost_bdt": round(shipping_cost_bdt, 2),
        "landed_cost_bdt": round(landed, 2),
        "suggested_wholesale_bdt": round(suggested_ws, 2),
        "suggested_retail_bdt": round(suggested_rt, 2),
    }
