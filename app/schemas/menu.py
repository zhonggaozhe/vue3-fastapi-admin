from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class MenuPermission(BaseModel):
    id: Optional[int] = None
    label: str
    value: str


class MenuPermissionPayload(BaseModel):
    label: str
    value: str


class MenuMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str
    title_key: Optional[str] = Field(default=None, alias="titleKey")
    icon: Optional[str] = None
    always_show: bool = Field(False, alias="alwaysShow")
    no_cache: bool = Field(False, alias="noCache")
    breadcrumb: bool = True
    affix: bool = False
    no_tags_view: bool = Field(False, alias="noTagsView")
    can_to: bool = Field(False, alias="canTo")
    active_menu: Optional[str] = Field(default=None, alias="activeMenu")
    hidden: bool = False


class MenuBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: int = Field(0, ge=0, le=1)
    parent_id: Optional[int] = Field(default=None, alias="parentId")
    name: str
    component: str
    path: str
    redirect: Optional[str] = None
    status: int = Field(1, ge=0, le=1)
    meta: MenuMeta
    permission_list: List[MenuPermission] = Field(default_factory=list, alias="permissionList")


class MenuCreate(MenuBase):
    pass


class MenuUpdate(MenuBase):
    pass


class MenuEditPayload(MenuUpdate):
    id: int


class MenuDeletePayload(BaseModel):
    ids: List[int]
    force: bool = False
