from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Course
from app.schemas.course import CourseDetailResponse, CourseListResponse

router = APIRouter(prefix="/courses", tags=["courses"])

@router.get("/test")
def list_courses():
    return {"zzz": status.HTTP_200_OK}




@router.get("", response_model=CourseListResponse)
def list_courses(db: Session = Depends(get_db)):
    courses = db.query(Course).order_by(Course.display_order.asc(), Course.id.asc()).all()
    return {"code": status.HTTP_200_OK, "message": "강의 목록 조회가 완료되었습니다.", "result": courses}


@router.get("/{course_id}", response_model=CourseDetailResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다.")
    return {"code": status.HTTP_200_OK, "message": "강의 상세 조회가 완료되었습니다.", "result": course}
