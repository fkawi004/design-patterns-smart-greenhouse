from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.application.commands.dto import CommandLogDto, CommandRequestDto
from src.application.commands.service import CommandService
from src.application.devices.errors import ActuatorNotFoundError
from src.domain.commands.base import UnknownCommandTypeError
from src.infrastructure.db import get_session
from src.interfaces.api.command_dependencies import build_command_service

router = APIRouter(prefix="/api/commands", tags=["commands"])


def get_command_service(session: Session = Depends(get_session)) -> CommandService:
    return build_command_service(session)


@router.post(
    "",
    response_model=CommandLogDto,
    responses={409: {"model": CommandLogDto, "description": "Command rejected by State"}},
)
def execute_command(
    request: CommandRequestDto,
    service: CommandService = Depends(get_command_service),
) -> CommandLogDto | JSONResponse:
    try:
        result = service.execute(
            request.command_type,
            request.device_id,
            request.payload,
        )
    except UnknownCommandTypeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ActuatorNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    if result.status == "rejected":
        return JSONResponse(status_code=409, content=jsonable_encoder(result))
    return result


@router.get("", response_model=list[CommandLogDto])
def list_command_history(
    limit: int = Query(default=50, ge=1, le=200),
    service: CommandService = Depends(get_command_service),
) -> list[CommandLogDto]:
    return service.list_history(limit)
