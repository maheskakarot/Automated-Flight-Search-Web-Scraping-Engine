import uuid

def uuid_generator():    
    # Generate a version 4 UUID
    generated_uuid = uuid.uuid4()
    # Convert the UUID to a string
    uuid_str = str(generated_uuid)
    return uuid_str