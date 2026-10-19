from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Script(SQLModel, table=True):
    """Represents an uploaded answer sheet."""
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    file_path: str
    status: str = Field(default="uploaded")  # status: uploaded, processing, completed, error
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationship to extracted regions
    regions: List["Region"] = Relationship(back_populates="script")

class Region(SQLModel, table=True):
    """Represents a single detected region (bounding box) on an answer sheet."""
    id: Optional[int] = Field(default=None, primary_key=True)
    script_id: int = Field(foreign_key="script.id")
    order_index: int
    region_type: str  # text, markdown_table, diagram
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    raw_ocr_text: Optional[str] = None
    refined_content: Optional[str] = None
    
    script: Optional[Script] = Relationship(back_populates="regions")