from fastapi import APIRouter
from transport.http.v1.schemas.ping import PingResponse
from application.ping_use_case import PingUseCase

router = APIRouter()

@router.get("/ping", response_model=PingResponse)
def ping():
    use_case = PingUseCase()
    result = use_case.execute()
    return PingResponse(message=result)
