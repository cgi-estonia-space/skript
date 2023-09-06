# skript
Convenient declarations for any CLI tool automatizer. Developed for processing EO data first-hand.

Very immature atm, see example.yaml for very basic usage.

## assets

### url

Currently, `http, https and S3` protocols are supported. For S3 credentials, please refer to [official documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html). One should provide credentials (keys or profile name) via environment variables.
