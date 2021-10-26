# Suppress AWS CLI Output
export AWS_PAGER=""

# Idle the Service that Spawns Tasks
aws ecs update-service --cluster "${CLUSTER}" --service "${SERVICE}" --desired-count 0

# Stop ECS Tasks
TASKS="$(aws ecs list-tasks --cluster "${CLUSTER}" --service "${SERVICE}" | grep "${CLUSTER}" || true | sed -e 's/"//g' -e 's/,//')"
for TASK in $TASKS; do
  ARN=$(echo $TASK | sed -e 's/"//g' -e 's/,//')
  aws ecs stop-task --cluster $CLUSTER --task "$ARN"
done