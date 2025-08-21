from bson import ObjectId

def serialize_doc(doc: dict) -> dict:
    """
    Convert ObjectId fields to strings recursively.
    """
    if not doc:
        return {}
    new_doc = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            new_doc[k] = str(v)
        elif isinstance(v, list):
            new_doc[k] = [serialize_doc(i) if isinstance(i, dict) else i for i in v]
        elif isinstance(v, dict):
            new_doc[k] = serialize_doc(v)
        else:
            new_doc[k] = v
    return new_doc


def serialize_list(docs: list) -> list:
    """
    Convert list of documents to serialized dicts.
    """
    return [serialize_doc(doc) for doc in docs]
