!/bin/sh

# ACME.SH Local Development (Update Email Address)
wget -O -  https://get.acme.sh | sh -s email=[EMAIL]

# Export from Default Profile:
export AWS_ACCESS_KEY_ID="$(aws configure get default.aws_access_key_id)"
export AWS_SECRET_ACCESS_KEY="$(aws configure get default.aws_secret_access_key)"
export AWS_SESSION_TOKEN="$(aws configure get default.aws_session_token)"

# AWS Region
export AWS_REGION=""

# DynamoDB Table Name for Ottr (Default: ottr)
export DYNAMODB_TABLE=""

# Route53 Hosted Zone ID for Host
export HOSTED_ZONE_ID=""

# FQDN of System for Ottr to Connect (FQDN: i.e. subdomain.example.com)
export HOSTNAME=""

# Certificate Common Name (CN: i.e. subdomain.example.com)
export COMMON_NAME=""

# Route53 Subdelegate Zone (i.e. example-acme.com)
export ACME_DNS=""

# Secrets Manager Prefix
export PREFIX=""

# Is There A Valid Certificate (Non-Self Signed) on the Target Host [True/False]
export VALIDATE_CERTIFICATE=""

# Certificate Signing Request Metadata
export organization=""
export organization_unit=""
export country=""
export state=""
export locality=""
export email=""

# Unset Environmental Variables
# unset AWS_ACCESS_KEY_ID AWS_SECRET_KEY AWS_SESSION_TOKEN AWS_REGION
# unset HOSTED_ZONE_ID DYNAMODB_TABLE ACME_DNS PREFIXN
# unset organization organization_unit country state locality email

# Execute As Parent Process:
# . ./environment.sh