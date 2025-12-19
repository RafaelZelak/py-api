from fastapi import APIRouter
from transport.http.v1.schemas.echo import EchoRequest, EchoResponse
from application.echo_use_case import EchoUseCase

router = APIRouter()

@router.post("/echo", response_model=EchoResponse)
def echo(request: EchoRequest):
    use_case = EchoUseCase()
    result = use_case.execute(request.message)
    return EchoResponse(message=result)
