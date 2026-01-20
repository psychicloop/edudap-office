from sqlalchemy import text
from . import db

def upsert_fts(quotation):
    """
    Updates or Inserts the quotation into the Full Text Search table.
    Uses 'INSERT OR REPLACE' because SQLite FTS5 does not support 'ON CONFLICT DO UPDATE'.
    """
    sql = """
        INSERT OR REPLACE INTO quotation_fts(
            rowid, 
            parsed_text, 
            brand, 
            make, 
            cas_no, 
            product_name, 
            instrument, 
            chemical, 
            reagent, 
            kit, 
            media
        ) VALUES (
            :id, 
            :parsed_text, 
            :brand, 
            :make, 
            :cas_no, 
            :product_name, 
            :instrument, 
            :chemical, 
            :reagent, 
            :kit, 
            :media
        )
    """
    
    # Execute the SQL with the data from the quotation object
    db.session.execute(text(sql), {
        'id': quotation.id,
        'parsed_text': quotation.parsed_text,
        'brand': quotation.brand or '',
        'make': quotation.make or '',
        'cas_no': quotation.cas_no or '',
        'product_name': quotation.product_name or '',
        'instrument': quotation.instrument or '',
        'chemical': quotation.chemical or '',
        'reagent': quotation.reagent or '',
        'kit': quotation.kit or '',
        'media': quotation.media or ''
    })
    db.session.commit()

def remove_fts(quotation):
    """
    Removes a quotation from the search index.
    """
    sql = "DELETE FROM quotation_fts WHERE rowid = :id"
    db.session.execute(text(sql), {'id': quotation.id})
    db.session.commit()

def query_fts(query_string):
    """
    Searches the FTS table for matching records.
    """
    sql = """
        SELECT rowid FROM quotation_fts 
        WHERE quotation_fts MATCH :query 
        ORDER BY rank
    """
    result = db.session.execute(text(sql), {'query': query_string})
    return [row[0] for row in result]
