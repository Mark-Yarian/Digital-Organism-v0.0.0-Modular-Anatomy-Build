import uuid
from digital_organism.core.utils import utc_now
def make_message(sender_id, sender_name, to, body, colony_id=None, audience="direct", message_type="message"):
    return {"message_id":"msg-"+uuid.uuid4().hex[:16],"colony_id":colony_id,"from":sender_id,"from_name":sender_name,"to":to,"audience":audience,"message_type":message_type,"created_at":utc_now(),"ttl":10,"body":body}
