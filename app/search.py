
from . import db
from .models import Quotation
from sqlalchemy import text

def ensure_fts():
    db.session.execute(text("CREATE VIRTUAL TABLE IF NOT EXISTS quotation_fts USING fts5(parsed_text, brand, make, cas_no, product_name, instrument, chemical, reagent, kit, media, content='');"))
    db.session.commit()


def upsert_fts(q:Quotation):
    sql = (
        "INSERT INTO quotation_fts(rowid, parsed_text, brand, make, cas_no, product_name, instrument, chemical, reagent, kit, media) "
        "VALUES (:id,:parsed_text,:brand,:make,:cas,:pname,:instrument,:chemical,:reagent,:kit,:media) "
        "ON CONFLICT(rowid) DO UPDATE SET parsed_text=:parsed_text, brand=:brand, make=:make, cas_no=:cas, "
        "product_name=:pname, instrument=:instrument, chemical=:chemical, reagent=:reagent, kit=:kit, media=:media"
    )
    db.session.execute(text(sql), {
        'id': q.id,
        'parsed_text': q.parsed_text or '',
        'brand': q.brand or '',
        'make': q.make or '',
        'cas': q.cas_no or '',
        'pname': q.product_name or '',
        'instrument': q.instrument or '',
        'chemical': q.chemical or '',
        'reagent': q.reagent or '',
        'kit': q.kit or '',
        'media': q.media or '',
    })
    db.session.commit()


def search_fts(query:str, limit:int=50):
    res = db.session.execute(text('SELECT rowid FROM quotation_fts WHERE quotation_fts MATCH :q LIMIT :lim'), {'q': query, 'lim': limit}).fetchall()
    ids = [r[0] for r in res]
    if not ids:
        return []
    return Quotation.query.filter(Quotation.id.in_(ids)).all()
