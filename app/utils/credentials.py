import os


def get_mail_credentials() -> dict:
    """!Should be changed when deployed to use some other SMTP server!"""
    
    # with open(project_folder() / "email_conf.yaml", "r") as yamlf:
        # credentials = yaml.safe_load(yamlf)
    mail_address = os.getenv("WPIG_MAIL_ADDRESS")
    mail_pass = os.getenv("WPIG_MAIL_PASSWORD")
        
    return({
        "mail_addr": mail_address,
        "mail_passwd": mail_pass,
    })