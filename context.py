import os

class Context:
    def __init__(self):
        self.altegio_api_url = None
        self.altegio_api_key = None
        self.altegio_company_id = None
        self.altegio_staff_id = None
        self.altegio_service_id = None
        
        self.dates_found_log_message = None

        self.email_from = None
        self.email_to = None
        self.email_subject = None
        self.email_body = None

        self.email_smtp_server = None
        self.email_smtp_port = None
        self.email_username = None
        self.email_password = None

        self.s3_bucket = None
        self.s3_key = None

        self.dates_filename = None

    def is_s3(self) -> bool:
        return self.s3_bucket is not None and self.s3_bucket != ''
    
    def is_file(self) -> bool:
        return self.dates_filename is not None and self.dates_filename != ''
    
    def is_email(self) -> bool:
        return self.email_smtp_server is not None and self.email_smtp_server != ''
    
    def is_terminal_message(self) -> bool:
        return self.dates_found_log_message is not None and self.dates_found_log_message != ''
    
def get_context():
    ctx = Context()
    vrs = vars(ctx)

    #set all the attributes of the ctx object, that are named after the .env keys
    for propname in filter(lambda a: not a.startswith('__'), vrs.keys()):
        vrs[propname] = os.getenv(propname.upper())

    return ctx