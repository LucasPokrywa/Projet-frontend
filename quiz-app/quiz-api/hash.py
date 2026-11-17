import hashlib

def HashGen(word: str) -> str:
    """ Génération d'un hash à partir d'une string passée en paramètre
    """
    return hashlib.md5(word.encode("utf-8")).hexdigest()

def HashCompare(hash: str, word: str) -> bool:
    """ Compare si le hash et la string passé en paramètre sont pareils
    """
    word_hashed = hashlib.md5(word.encode("utf-8")).hexdigest()
    if hash == word_hashed:
        return True
    else:
        return False

