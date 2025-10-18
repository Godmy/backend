from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from core.models.base import BaseModel  # Изменяем импорт


class PermissionModel(BaseModel):
    __tablename__ = "permissions"

    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    resource = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)
    scope = Column(String(20), default="own")

    # Связи
    role = relationship("RoleModel", back_populates="permissions")
