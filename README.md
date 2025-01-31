# Alteg.io checker

This is a small AWS lambda & S3 compatible python script for checking available dates on [alteg.io](https://alteg.io) date reservation sites commonly used by hairdressers, nail techs and other service providers. It is capable of running as an AWS lambda service (further details below), and it sends emails for any new dates it finds. 

It uses the alteg.io API, for which you have to request access. For further details, see the [API documentation](https://developer.alteg.io/api).

## How it works
By default it sends an email to an email address you specify with the new dates found. During repeated calls (for example, by setting up your AWS lambda to be called every n minutes), it also saves the dates it previously found, and only sends notifications if it finds dates that it hasn't seen before.

## AWS integration
I have this code running as an AWS lambda "service". My setup has an AWS EventBridge rule that calls the lambda function every 5 minutes, which runs the code, saves the dates it finds to S3, and sends an email if it finds any new dates.

For details on how to set up a lambda function to be called every N minutes, see this [tutorial by AWS](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-run-lambda-schedule.html).

For details on how to allow your lambda function to access S3, see this [other tutorial by AWS](https://repost.aws/knowledge-center/lambda-execution-role-s3-bucket).

## Installation (local)
0. Copy the clone URL of this repo by clicking the "Code" button on the top right, and click the copy button next to the GitHub repo URL.
1. In a terminal run: `git clone [URL you just copied]`
2. `cd altegio_check`
3. Create a virtual environment: `python -m venv ./my_venv`
4. Activate the virtual environment: 
   - On windows: `./my_venv/Scripts/activate.ps1`
   - On unix-based systems: `source ./my_venv/bin/activate`
5. Install requirements: `pip install -r requirements.txt`
6. Set the environment variables (see [below](#configuration))
7. Run the app: `python ./lambda_function.py`

## Installation (AWS & S3)
0. Follow the local installation instructions above
1. Follow [this tutorial](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-run-lambda-schedule.html) for instructions on how to set up an AWS lambda function that will be called every N minutes
2. Follow this [other tutorial](https://repost.aws/knowledge-center/lambda-execution-role-s3-bucket) to allow the lambda function access to S3
3. Use `pip show boto3` to see where pip installed packages in your local environment - check the "Location: ..." line (in my case, it was `altegio_check/my_venv/Lib/site-packages`)
4. Create a zip file with the dependencies and code: 
   - include everything in the folder found above
   - include `lambda_function.py`, `context.py`, and `.env`
5. Upload the created .zip file to AWS lambda:
   - with your lambda function open, use the "Upload from" button, select ".zip file", and select the .zip file you just created
   - click the "Deploy" button in the integrated code editor in the lambda window

For further instructions on how to deploy python .zip packages to lambda, see [this link](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-create-dependencies).

## <a name="configuration"></a>Configuration
The script can be configured with a .env file. An example file is provided named `.env.example`. You need to make a copy of this named `.env`, and you can edit the details in it.

The structure of this file is as follows:
 - Alteg.io API details:
   - ALTEGIO_API_URL: the api url to call (filled by default)
   - ALTEGIO_API_KEY: the api key for (bearer) authentication
   - ALTEGIO_{COMPANY|STAFF|SERVICE}_ID: company, staff, and service id for the specific service you want the script to check

 - DATES_FOUND_LOG_MESSAGE: message to write into console if you want the script to just write notifications to console (without email)
 - Email details:
   - EMAIL_{FROM|TO}: email address to send notifications from/to
   - EMAIL_SUBJECT: subject of the email to send
   - EMAIL_RESERVATION_URL: url to include in the email body, where users can reserve dates
   - EMAIL_BODY: body of the email. An example is included in `.env.example`. Available placeholders: 
     - ${EMAIL_RESERVATION_URL}: where to include the reservation link above
     - {dates}: where to include the newly found dates
   
   - EMAIL_SMTP_{SERVER|PORT}: smtp server & port for sending emails
   - EMAIL_{USERNAME|PASSWORD}: smtp username & password

 - DATES_FILENAME: path to a file where previously found dates should be saved
 - S3 settings:
   - S3_BUCKET: name of S3 bucket where files should be saved
   - S3_KEY: name of S3 object in the bucket that should be written
