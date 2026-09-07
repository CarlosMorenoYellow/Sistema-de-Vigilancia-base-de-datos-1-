from fastapi import APIRouter, Depends
from typing import List
from app.database import get_db_connection
from app.schemas.vectors import VectorSearchRequest, VectorSearchResult

router = APIRouter(tags=["Búsqueda Vectorial"])

@router.post("/search/similar", response_model=List[VectorSearchResult], summary="Buscar objetos por embedding")
def search_similar_objects(req: VectorSearchRequest, conn=Depends(get_db_connection)):
    with conn.cursor() as cur:
        vector_str = f"[{','.join(map(str, req.vector))}]"
        cur.execute(
            """
            SELECT id, type, color, (embedding <=> %s::vector) AS distance
            FROM OBJECT
            WHERE embedding IS NOT NULL
              AND (%s::text IS NULL OR type = %s::OBJECT_TYPE)
            ORDER BY distance ASC
            LIMIT %s;
            """,
            (vector_str, req.tipo, req.tipo, req.limit)
        )
        return cur.fetchall()