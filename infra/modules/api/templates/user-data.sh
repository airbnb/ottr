#!/bin/bash

echo ECS_CLUSTER=${cluster_name} >> /etc/ecs/ecs.config
docker plugin install rexray/ebs REXRAY_PREEMPT=true EBS_REGION=${region} --grant-all-permissions
