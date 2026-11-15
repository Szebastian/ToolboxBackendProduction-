import secrets
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from src.features.delegation_tokens.domain.delegation_token import DelegationToken
from src.features.delegation_tokens.domain.ports.delegation_token_repository_port import IDelegationTokenRepository
from src.features.delegation_tokens.domain.ports.messaging_notifier_port import IMessagingNotifier
from src.features.delegation_tokens.application.dtos.delegation_dtos import DelegateRequestInputDTO, DelegateRequestOutputDTO

class DelegateRequestToMechanicUseCase:
    def __init__(
        self,
        token_repo: IDelegationTokenRepository,
        messaging_notifier: IMessagingNotifier,
        frontend_base_url: str
    ):
        self.token_repo = token_repo
        self.messaging_notifier = messaging_notifier
        self.frontend_base_url = frontend_base_url

    async def execute(self, dto: DelegateRequestInputDTO) -> DelegateRequestOutputDTO:
        raw_token = secrets.token_hex(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        duration = dto.duration_hours or 48
        expires_at = datetime.now(timezone.utc) + timedelta(hours=duration)

        delegation_token = DelegationToken(
            id=str(uuid.uuid4()),
            parts_request_id=dto.parts_request_id,
            token_hash=token_hash,
            raw_token=raw_token,
            mechanic_phone=dto.mechanic_phone,
            mechanic_name=dto.mechanic_name,
            expires_at=expires_at
        )

        await self.token_repo.create(delegation_token)

        access_url = f"{self.frontend_base_url}/guest/mechanic?token={raw_token}"

        await self.messaging_notifier.send_whatsapp_delegation_link(
            phone=dto.mechanic_phone,
            mechanic_name=dto.mechanic_name,
            direct_url=access_url
        )

        return DelegateRequestOutputDTO(
            token_id=delegation_token.id,
            access_url=access_url,
            expires_at=expires_at.isoformat()
        )
