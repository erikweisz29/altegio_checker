import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
import smtplib
import logging
import json
import os

import requests
import boto3
from dotenv import load_dotenv

from context import Context, get_context

def send_message(ctx: Context, new_dates: set):
    if ctx.is_email():
        try:
            message = MIMEMultipart()
            message["From"] = ctx.email_from
            message["To"] = ctx.email_to
            message["Subject"] = ctx.email_subject

            new_dates_str = ", ".join(sorted(new_dates))
            body = ctx.email_body.replace("{dates}", new_dates_str)
            
            message.attach(MIMEText(body, 'plain'))
            text = message.as_string()

            s = smtplib.SMTP(ctx.email_smtp_server, int(ctx.email_smtp_port))
            s.starttls()
            s.login(ctx.email_username, ctx.email_password)
            s.sendmail(ctx.email_from, ctx.email_to, text)
            s.quit()

        except Exception as ex:
            err_msg = "An error occurred while sending the email!"
            logging.exception(err_msg)
            raise RuntimeError(err_msg) from ex
    elif ctx.is_terminal_message():
        logging.info(ctx.dates_found_log_message)
    
def check_dates(ctx: Context) -> bool:
    date_now_fmt = datetime.datetime.now().strftime("%Y-%m-%d")
    js = None

    try:
        url = ctx.altegio_api_url + ctx.altegio_company_id
        headers = {
            "Authorization" : f"Bearer {ctx.altegio_api_key}", 
            "Content-Type" : "application/json", 
            "Accept" : "application/vnd.api.v2+json"
        }
        params = {
            "staff_id": ctx.altegio_staff_id, 
            "service_ids[]": ctx.altegio_service_id,
            "date_from": date_now_fmt
        }
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()

        if data["success"] == True:
            js = data["data"]["booking_dates"]
            return compare_and_update_dates(js, ctx)
        else:
            err_msg = "Failed to query data from alteg.io API!"
            logging.error(err_msg)
            return False

    except Exception as ex:
        err_msg = "An error occurred while making the web requests!"
        logging.exception(err_msg)
        raise RuntimeError(err_msg) from ex

# Compares the previous dates saved with the current dates
# If they are different, writes the new dates (even if there are none)
# Returns the new dates if an email needs to be sent (if there are dates, and they are different), and None otherwise.
def compare_and_update_dates(current_json, ctx) -> set|None:
    booking_dates = current_json["booking_dates"]
    booking_dates_set = set(booking_dates)

    prev_dates = get_previous_dates(ctx)
    prev_dates_set = set(prev_dates)

    if prev_dates_set != booking_dates_set:
        write_dates(booking_dates, ctx)

        # If the sets are different, but the new set is a subset of the old set, 
        # then there must be less dates now, in which case we do not need to send a notification.
        are_there_less_dates = booking_dates_set.issubset(prev_dates_set)
        if len(booking_dates) > 0 and not are_there_less_dates:
            # Return new dates
            set_diff = prev_dates_set.difference(booking_dates_set)
            return set_diff
    
    return None

def get_previous_dates(ctx: Context) -> list:
    prev = None

    # If S3 bucket is set, use S3
    if ctx.is_s3():
        try:
            if ctx.s3_key is None or ctx.s3_key == '':
                raise RuntimeError("S3 key not set!")
            
            s3 = boto3.resource('s3')
            obj = s3.Object(ctx.s3_bucket, ctx.s3_key)
            prev = json.load(obj.get()['Body'])
        except Exception:
            err_msg = "An error occurred while retrieving previous dates from S3!"
            logging.exception(err_msg)
            prev = []

    # Otherwise, use local file
    elif ctx.is_file():
        try:
            if not os.path.exists(ctx.dates_filename):
                prev = []
            else:
                with open(ctx.dates_filename, "r", encoding="utf-8") as file:
                    prev = json.load(file)
        except Exception:
            err_msg = "An error occurred while reading previous dates from the specified file!"
            logging.exception(err_msg)
            prev = []

    else:
        raise RuntimeError("Neither S3 or local filename is set!")
    
    if type(prev) is list:
        return prev
    else:
        return []
    
def write_dates(dates: list, ctx: Context):
    dump = json.dumps(dates)
    byte_dump = dump.encode()

    if ctx.is_s3():
        try:
            s3 = boto3.resource('s3')
            obj = s3.Object(ctx.s3_bucket, ctx.s3_key)
            obj.put(Body=byte_dump)
            logging.info(f"Updated s3 object with the following data: {dates}")
        except Exception:
            err_msg = "An error occurred while writing dates to S3!"
            logging.exception(err_msg)

    elif ctx.is_file():
        try:
            with open(ctx.dates_filename, "wb") as file:
                file.write(byte_dump)

            logging.info(f"Updated file with the following data: {dates}")
        except Exception:
            err_msg = "An error occurred while writing dates to the specified file!"
            logging.exception(err_msg)

def lambda_handler(event, context):
    # https://stackoverflow.com/a/56579088
    if len(logging.getLogger().handlers) > 0:
        # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
        # `.basicConfig` does not execute. Thus we set the level directly.
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)
    
    load_dotenv()
    ctx = get_context()

    new_dates = check_dates(ctx)
    if new_dates is not None:
        send_message(ctx, new_dates)
        return f"Dates found, email sent!"
    else:
        return "Dates not found, email not sent"
    
if __name__=="__main__":
    lambda_handler("asd", "asd")