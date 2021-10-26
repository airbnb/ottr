import boto3
import pytest

from moto.route53 import mock_route53
from otter.router.src.shared.client import get_acme_challenge_records

@pytest.fixture
def _init_dns():
    @mock_route53
    def route53_client():
        conn = boto3.client("route53", region_name="us-east-1")
        # Subdelegate Zone
        conn.create_hosted_zone(
            Name="example-acme.com.",
            CallerReference=str(hash("foo")),
            HostedZoneConfig=dict(
                PrivateZone=True, Comment="Subdelegate Zone"),
        )

        # Main Hosted Zone
        conn.create_hosted_zone(
            Name="example.com.",
            CallerReference=str(hash("bar")),
            HostedZoneConfig=dict(
                PrivateZone=True, Comment="Subdelegate Zone"),
        )

        # example.com Route53 Hosted Zone ID
        hosted_zone_id = conn.list_hosted_zones_by_name(
            DNSName="example.com.").get('HostedZones')[0].get('Id').split('/')[-1]

        # Create CNAME Mapping _acme-challenge.subdomain.example.com =>
        # _acme-challenge.example-acme.com
        cname_record_endpoint_payload = {
            "Comment": "Create CNAME record _acme-challenge.airbnb.example.com",
            "Changes": [
                {
                    "Action": "CREATE",
                    "ResourceRecordSet": {
                        "Name": "_acme-challenge.subdomain.example.com.",
                        "Type": "CNAME",
                        "TTL": 10,
                        "ResourceRecords": [{"Value": "_acme-challenge.example-acme.com."}],
                    },
                }
            ],
        }

        conn.change_resource_record_sets(
            HostedZoneId=hosted_zone_id, ChangeBatch=cname_record_endpoint_payload
        )

        # Create CNAME Mapping _acme-challenge.secondary.example.com =>
        # _acme-challenge.example-acme.com
        cname_record_endpoint_payload = {
            "Comment": "Create CNAME record _acme-challenge.secondary.example.com",
            "Changes": [
                {
                    "Action": "CREATE",
                    "ResourceRecordSet": {
                        "Name": "_acme-challenge.secondary.example.com.",
                        "Type": "CNAME",
                        "TTL": 10,
                        "ResourceRecords": [{"Value": "_acme-challenge.example-acme.com."}],
                    },
                }
            ],
        }

        conn.change_resource_record_sets(
            HostedZoneId=hosted_zone_id, ChangeBatch=cname_record_endpoint_payload
        )
        return hosted_zone_id
    return route53_client

@mock_route53
def test_route53_subdelegate_zone(_init_dns):
    hosted_zone_id = _init_dns()
    # Validate Mapping Exists, Return Set of All Valid Hosts
    input = []
    input.append(hosted_zone_id)
    hosts = get_acme_challenge_records(input)
    assert hosts == {'subdomain.example.com', 'secondary.example.com'}

@mock_route53
def test_route53_inalid_subdelegate_zone(_init_dns):
    _init_dns()
    hosted_zone_id = "XXXXX"
    input = []
    input.append(hosted_zone_id)

    hosts = get_acme_challenge_records(input)
