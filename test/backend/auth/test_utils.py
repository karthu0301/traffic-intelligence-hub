from backend.auth import utils

def test_password_hash_and_verify():
    password = "secret"
    hashed = utils.bcrypt.hash(password)
    assert utils.bcrypt.verify(password, hashed)
