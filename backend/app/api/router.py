from fastapi import APIRouter
from app.api.endpoints import auth, accounts, transactions, receipts, imports, households, budgets, rules, tags

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(receipts.router, prefix="/receipts", tags=["receipts"])
api_router.include_router(imports.router, prefix="/imports", tags=["imports"])
api_router.include_router(households.router, prefix="/households", tags=["households"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
