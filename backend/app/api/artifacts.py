from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid

from ..database import get_db
from ..models import Artifact, ArtifactVersion, User, Session as DBSession
from .auth import get_current_user

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


class ArtifactResponse(BaseModel):
    id: str
    session_id: str
    title: str
    type: str
    current_version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArtifactDetailResponse(BaseModel):
    id: str
    session_id: str
    title: str
    type: str
    current_version: int
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArtifactVersionResponse(BaseModel):
    id: str
    artifact_id: str
    version: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[ArtifactResponse])
async def list_artifacts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出当前用户的所有产物"""
    result = await db.execute(
        select(Artifact)
        .where(Artifact.user_id == current_user.id)
        .order_by(Artifact.updated_at.desc())
    )
    artifacts = result.scalars().all()
    return [
        ArtifactResponse(
            id=a.id,
            session_id=a.session_id,
            title=a.name,
            type=a.artifact_type,
            current_version=a.current_version,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in artifacts
    ]


@router.get("/{artifact_id}", response_model=ArtifactDetailResponse)
async def get_artifact(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取特定产物"""
    result = await db.execute(
        select(Artifact).where(
            Artifact.id == artifact_id,
            Artifact.user_id == current_user.id
        )
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="产物不存在")

    latest_version_result = await db.execute(
        select(ArtifactVersion)
        .where(
            ArtifactVersion.artifact_id == artifact_id,
            ArtifactVersion.version == artifact.current_version
        )
        .order_by(ArtifactVersion.created_at.desc())
        .limit(1)
    )
    latest_version = latest_version_result.scalar_one_or_none()
    content = latest_version.content if latest_version else ""

    return ArtifactDetailResponse(
        id=artifact.id,
        session_id=artifact.session_id,
        title=artifact.name,
        type=artifact.artifact_type,
        current_version=artifact.current_version,
        content=content,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: str,
    version: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """下载产物文件"""
    result = await db.execute(
        select(Artifact).where(
            Artifact.id == artifact_id,
            Artifact.user_id == current_user.id
        )
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="产物不存在")

    download_version = version if version else artifact.current_version

    version_result = await db.execute(
        select(ArtifactVersion).where(
            ArtifactVersion.artifact_id == artifact_id,
            ArtifactVersion.version == download_version
        )
    )
    version_record = version_result.scalar_one_or_none()
    if not version_record:
        raise HTTPException(status_code=404, detail="指定版本不存在")

    if artifact.artifact_type == "requirement_spec":
        content_type = "application/json"
        extension = "json"
    elif artifact.artifact_type == "markdown":
        content_type = "text/markdown"
        extension = "md"
    else:
        content_type = "text/plain"
        extension = "txt"

    filename = f"{artifact.name}_v{download_version}.{extension}"

    return Response(
        content=version_record.content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{artifact_id}/versions", response_model=List[ArtifactVersionResponse])
async def get_artifact_versions(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取产物的所有版本"""
    result = await db.execute(
        select(Artifact).where(
            Artifact.id == artifact_id,
            Artifact.user_id == current_user.id
        )
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="产物不存在")

    versions_result = await db.execute(
        select(ArtifactVersion)
        .where(ArtifactVersion.artifact_id == artifact_id)
        .order_by(ArtifactVersion.version.desc())
    )
    versions = versions_result.scalars().all()

    return [
        ArtifactVersionResponse(
            id=v.id,
            artifact_id=v.artifact_id,
            version=v.version,
            content=v.content,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.post("", response_model=ArtifactResponse)
async def create_artifact(
    session_id: str,
    name: str,
    artifact_type: str,
    content: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新产物"""
    session_result = await db.execute(
        select(DBSession).where(
            DBSession.id == session_id,
            DBSession.user_id == current_user.id
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    artifact_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())

    artifact = Artifact(
        id=artifact_id,
        session_id=session_id,
        user_id=current_user.id,
        name=name,
        artifact_type=artifact_type,
        current_version=1,
    )
    db.add(artifact)

    artifact_version = ArtifactVersion(
        id=version_id,
        artifact_id=artifact_id,
        version=1,
        content=content,
    )
    db.add(artifact_version)

    await db.commit()

    return ArtifactResponse(
        id=artifact.id,
        session_id=artifact.session_id,
        title=artifact.name,
        type=artifact.artifact_type,
        current_version=artifact.current_version,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


@router.put("/{artifact_id}", response_model=ArtifactResponse)
async def update_artifact(
    artifact_id: str,
    content: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新产物内容（创建新版本）"""
    result = await db.execute(
        select(Artifact).where(
            Artifact.id == artifact_id,
            Artifact.user_id == current_user.id
        )
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="产物不存在")

    new_version = artifact.current_version + 1
    artifact.current_version = new_version

    version_id = str(uuid.uuid4())
    artifact_version = ArtifactVersion(
        id=version_id,
        artifact_id=artifact_id,
        version=new_version,
        content=content,
    )
    db.add(artifact_version)

    await db.commit()

    return ArtifactResponse(
        id=artifact.id,
        session_id=artifact.session_id,
        title=artifact.name,
        type=artifact.artifact_type,
        current_version=artifact.current_version,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


@router.delete("/{artifact_id}")
async def delete_artifact(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除产物"""
    result = await db.execute(
        select(Artifact).where(
            Artifact.id == artifact_id,
            Artifact.user_id == current_user.id
        )
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="产物不存在")

    await db.delete(artifact)
    await db.commit()

    return {"message": "产物已删除"}
