from __future__ import annotations

import sqlite3

from database import DB_PATH
from domain.repositories.maps_existing_keys_repository import ExistingMapsKeys, MapsExistingKeysRepository


class SqliteMapsExistingKeysRepository(MapsExistingKeysRepository):
    def get_existing_maps_keys(self) -> ExistingMapsKeys:
        try:
            from services.maps_scrape_service import derive_maps_place_id
        except Exception:
            derive_maps_place_id = None

        prospeccao_keys: set[str] = set()
        lead_keys: set[str] = set()

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute(
            "SELECT maps_place_id, maps_url FROM prospeccao_temp WHERE ((maps_place_id IS NOT NULL AND maps_place_id != '') OR (maps_url IS NOT NULL AND maps_url != '')) AND (arquivado = 0 OR arquivado IS NULL)"
        )
        for row in c.fetchall() or []:
            mpid = (row["maps_place_id"] or "").strip()
            if mpid:
                prospeccao_keys.add(mpid)
            mu = (row["maps_url"] or "").strip()
            if derive_maps_place_id and mu:
                try:
                    dk = derive_maps_place_id(mu)
                except Exception:
                    dk = ""
                if dk:
                    prospeccao_keys.add(dk)

        try:
            c.execute(
                "SELECT maps_place_id, maps_url FROM leads WHERE (maps_place_id IS NOT NULL AND maps_place_id != '') OR (maps_url IS NOT NULL AND maps_url != '')"
            )
            for row in c.fetchall() or []:
                mpid = (row["maps_place_id"] or "").strip()
                if mpid:
                    lead_keys.add(mpid)
                mu = (row["maps_url"] or "").strip()
                if derive_maps_place_id and mu:
                    try:
                        dk = derive_maps_place_id(mu)
                    except Exception:
                        dk = ""
                    if dk:
                        lead_keys.add(dk)
        except Exception:
            pass
        finally:
            conn.close()

        return ExistingMapsKeys(prospeccao_keys=prospeccao_keys, lead_keys=lead_keys)
