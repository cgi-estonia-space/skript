import boto3
import os
import requests
from tqdm import tqdm


def get_filename_from_url(url):
    # Send a HEAD request to the URL to retrieve headers
    response = requests.head(url)

    # Check if the request was successful (HTTP status code 200)
    if response.status_code == 200:
        # Try to get the filename from the Content-Disposition header
        content_disposition = response.headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('\'"')
        else:
            # If the header is not available, extract the filename from the URL
            filename = url.split("/")[-1]

        return filename
    else:
        print(f"Failed to retrieve headers for {url}, status code: {response.status_code}")
        return None


def download_http(url, save_directory):
    filename = get_filename_from_url(url)

    if filename:
        save_path = os.path.join(save_directory, filename)

        response = requests.get(url, stream=True)

        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))

            with open(save_path, 'wb') as file, tqdm(
                    desc=filename,
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    file.write(data)
                    bar.update(len(data))

            return filename
        else:
            print(f"Failed to download {url}, status code: {response.status_code}")
            return None
    else:
        return None


def download_s3(uri, save_directory):
    parts = uri.split('/')
    bucket_name = parts[2]
    object_key = '/'.join(parts[3:])
    filename = parts[-1]
    # Initialize the S3 client
    s3 = boto3.client('s3')

    # Specify the file path where you want to save the downloaded file
    save_path = os.path.join(save_directory, object_key.split('/')[-1])

    # Download the file from S3
    file_size = s3.head_object(Bucket=bucket_name, Key=object_key)['ContentLength']

    # Define the chunk size for downloading
    chunk_size = 1024 * 1024  # 1 MB chunks
    start_byte = 0

    with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
        with open(save_path, 'wb') as f:
            while start_byte < file_size:
                end_byte = min(start_byte + chunk_size - 1, file_size - 1)

                range_header = f'bytes={start_byte}-{end_byte}'
                chunk = s3.get_object(Bucket=bucket_name, Key=object_key, Range=range_header)['Body'].read()
                f.write(chunk)

                start_byte = end_byte + 1
                pbar.update(len(chunk))

    return filename


def get_uri_type(uri):
    if uri.startswith("http://") or uri.startswith("https://"):
        return download_http
    elif uri.startswith("ftp://"):
        return None
    elif uri.startswith("s3://"):
        return download_s3
    else:
        return None


def fetch(uri, save_directory):
    fetcher = get_uri_type(uri)
    if fetcher is None:
        raise RuntimeError(f"Given URI - {uri} is not supported currently")

    print(f"Downloading {uri} to {save_directory}")
    return fetcher(uri, save_directory)
