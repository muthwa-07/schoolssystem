
# Does Not use a Salt
import hashlib
def hash_password(password):
       # Create a new md5 hash object
       hasher = hashlib.md5()
       # Hash the password
       hasher.update(password.encode('utf-8'))
       # Get the hexadecimal representation of the hash
       hashed_password = hasher.hexdigest()
       return hashed_password




# uses a salt
import hashlib
def hash_password_salt(password):
        # Concatenate the salt and password
        salt = "QW66HJk(994634vv)"
        salted_password = salt + password
        # Create an MD5 hash object
        md5_hasher = hashlib.md5()
        # Update the hash object with the salted password
        md5_hasher.update(salted_password.encode('utf-8'))
        # Get the hexadecimal digest of the hash
        hashed_password = md5_hasher.hexdigest()
        return hashed_password




def verify_password_salt(hashed_password, input_password):
        # Get the salt used during hashing
        salt = "QW66HJk(994634vv)"
        # Concatenate the salt and input password
        salted_input_password = salt + input_password
        # Hash the salted input password
        hashed_input_password = hashlib.md5(salted_input_password.encode('utf-8')).hexdigest()
        # Compare the stored hashed password with the hashed input password
        return hashed_password == hashed_input_password
