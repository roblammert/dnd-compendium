from app.services import canonical_checksum, slugify

def test_slugify(): assert slugify("Ancient Red Dragon!")=="ancient-red-dragon"
def test_checksum_is_stable(): assert canonical_checksum({"b":2,"a":1})==canonical_checksum({"a":1,"b":2})
