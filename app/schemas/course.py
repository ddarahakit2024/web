from pydantic import BaseModel, ConfigDict


class CurriculumSection(BaseModel):
    title: str
    lessons: list[str]


class CourseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    instructor_name: str
    category: str
    price_krw: int
    thumbnail_url: str
    summary: str


class CourseDetail(CourseListItem):
    description: str
    curriculum: list[CurriculumSection]


class CourseListResponse(BaseModel):
    code: int
    message: str
    result: list[CourseListItem]


class CourseDetailResponse(BaseModel):
    code: int
    message: str
    result: CourseDetail
