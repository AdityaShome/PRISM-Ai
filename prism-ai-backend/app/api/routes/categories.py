from fastapi import APIRouter

from app.schemas.scan import CategoryListItem

router = APIRouter(prefix="/api", tags=["categories"])


@router.get("/categories", response_model=list[CategoryListItem])
def get_categories() -> list[CategoryListItem]:
    return [
        CategoryListItem(category="internships", title="Internships", description="Real internship scam analysis", supported=True, status="live"),
        CategoryListItem(category="scholarships", title="Scholarships", description="Coming soon", supported=False, status="coming_soon"),
        CategoryListItem(category="pg_listings", title="PG Listings", description="Coming soon", supported=False, status="coming_soon"),
        CategoryListItem(category="hackathons", title="Hackathons", description="Coming soon", supported=False, status="coming_soon"),
        CategoryListItem(category="used_laptops", title="Used Laptops", description="Coming soon", supported=False, status="coming_soon"),
        CategoryListItem(category="courses", title="Courses", description="Coming soon", supported=False, status="coming_soon"),
    ]
