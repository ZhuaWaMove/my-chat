from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.news import Category, CategoryCreate, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter()


@router.get("/", response_model=List[Category])
def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    db: Session = Depends(get_db)
):
    """获取分类列表"""
    service = CategoryService(db)
    return service.get_categories(skip=skip, limit=limit, search=search)


@router.get("/{category_id}", response_model=Category)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """根据ID获取分类"""
    service = CategoryService(db)
    category = service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/", response_model=Category, status_code=201)
def create_category(category_data: CategoryCreate, db: Session = Depends(get_db)):
    """创建分类"""
    service = CategoryService(db)
    try:
        return service.create_category(category_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{category_id}", response_model=Category)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db)
):
    """更新分类"""
    service = CategoryService(db)
    try:
        category = service.update_category(category_id, category_data)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """删除分类"""
    service = CategoryService(db)
    try:
        success = service.delete_category(category_id)
        if not success:
            raise HTTPException(status_code=404, detail="Category not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{category_id}/stats")
def get_category_stats(category_id: int, db: Session = Depends(get_db)):
    """获取分类统计信息"""
    service = CategoryService(db)
    try:
        return service.get_category_stats(category_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/all/with-counts")
def get_all_categories_with_counts(db: Session = Depends(get_db)):
    """获取所有分类及其计数"""
    service = CategoryService(db)
    return service.get_all_categories_with_counts()