"""Intervalo de datas YYYY-MM-DD (UTC naive) para filtros de admin/dashboard/conversas."""
from datetime import datetime
from typing import Optional, Tuple

from fastapi import HTTPException, status


def parse_stats_date_range(
    date_from: Optional[str],
    date_to: Optional[str],
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Converte YYYY-MM-DD em intervalo em UTC naive (alinhado a datetime.utcnow no app).

    - Nenhuma data → sem filtro.
    - Só «de» ou só «até» → **um único dia civil** (00:00:00 a 23:59:59.999999 desse dia em UTC).
      (Antes, só «de» ia até hoje e parecia não filtrar; só «até» vinha de 1970.)
    - «De» e «até» → do início do primeiro dia ao fim do último dia (ambos inclusivos).
    """
    def _one(s: Optional[str]) -> Optional[datetime]:
        if not s or not str(s).strip():
            return None
        raw = str(s).strip()[:10]
        try:
            return datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Datas devem estar no formato YYYY-MM-DD.",
            )

    df = _one(date_from)
    dt = _one(date_to)
    if df is None and dt is None:
        return None, None

    def _end_of_day(d: datetime) -> datetime:
        return d.replace(hour=23, minute=59, second=59, microsecond=999999)

    def _start_of_day(d: datetime) -> datetime:
        return d.replace(hour=0, minute=0, second=0, microsecond=0)

    if df is not None and dt is None:
        s = _start_of_day(df)
        e = _end_of_day(df)
        return s, e

    if df is None and dt is not None:
        s = _start_of_day(dt)
        e = _end_of_day(dt)
        return s, e

    day_start = _start_of_day(df)
    day_end = _end_of_day(dt)
    if day_start > day_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data inicial não pode ser posterior à data final.",
        )
    return day_start, day_end
