import json

import boto3
import pytest
from moto import mock_ecs
from moto import mock_ec2
from moto.ec2 import utils as ec2_utils

# from otter.router.src.shared.client import ECSClient
from otter.router.src.shared.device import Device
from tests.unit import EXAMPLE_AMI_ID


@pytest.fixture
def _init_cluster():
    @mock_ecs
    @mock_ec2
    def cluster():
        # ECS Cluster
        test_cluster_name = 'otter'
        client = boto3.client("ecs", region_name="us-east-1")
        response = client.create_cluster(clusterName=test_cluster_name)

        # EC2 Backed Instances for ECS Cluster
        ec2 = boto3.resource("ec2", region_name="us-east-1")
        test_instance = ec2.create_instances(
            ImageId=EXAMPLE_AMI_ID, MinCount=1, MaxCount=1
        )[0]

        instance_id_document = json.dumps(
            ec2_utils.generate_instance_identity_document(test_instance)
        )

        # Register EC2 Instances to ECS Cluster
        client.register_container_instance(
            cluster=test_cluster_name, instanceIdentityDocument=instance_id_document
        )

        # Create ECS Task Definition
        client.register_task_definition(
            family='otter-panos-9x-lets-encrypt',
            taskRoleArn='arn:aws:iam::123456789012:role/otter-role',
            executionRoleArn='arn:aws:iam::123456789012:role/otter-role',
            containerDefinitions=[
                {
                    "volumesFrom": [],
                    "memory": 512,
                    "portMappings": [],
                    "essential": True,
                    "mountPoints": [],
                    "name": "otter",
                    "environment": [],
                    "image": "image:latest",
                    "cpu": 1,
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/otter",
                            "awslogs-region": "us-east-1",
                            "awslogs-stream-prefix": "/otter-panos-9x-lets-encrypt}"
                        }
                    }
                }
            ]
        )

        return client
    return cluster
