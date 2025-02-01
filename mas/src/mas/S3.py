import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError

load_dotenv()

def upload_files_to_s3(directory, bucket_name, s3_folder='outputs/'):
    s3 = boto3.client('s3')
    
    for filename in os.listdir(directory):
        if filename.endswith('.md'):
            local_path = os.path.join(directory, filename)
            s3_path = os.path.join(s3_folder, filename)
            
            try:
                s3.upload_file(local_path, bucket_name, s3_path)
                print(f'Successfully uploaded {filename} to {bucket_name}/{s3_path}')
            except FileNotFoundError:
                print(f'The file {filename} was not found')
            except NoCredentialsError:
                print('Credentials not available')