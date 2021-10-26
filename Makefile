PATH := ${PATH}:/usr/bin:/usr/local/bin:/Library/Developer/CommandLineTools/usr/bin

CURRENT_DIR = $(shell pwd)
OS_VERSION = $(shell uname)

VERSION := $(shell git describe --tags --always)

CONTAINERS_DIR = platforms
CONTAINERS_PREFIX = otter

CONTAINERS = $(shell find $(CONTAINERS_DIR) -type d -name template -prune -o -mindepth 1 -maxdepth 1 -exec basename {} \;)

.check-api-args:
ifndef PREFIX
	$(error PREFIX is not set. please use `make {XXX} PREFIX=<YOUR_PREFIX>.`)
endif
ifndef AWS_ACCOUNT_ID
	$(error AWS_ACCOUNT_ID is not set. please use `make {XXX} AWS_ACCOUNT_ID=<YOUR_PREFIX>.`)
endif
ifndef AWS_REGION
	$(error AWS_REGION is not set. please use `make {XXX} AWS_REGION=<YOUR_PREFIX>.`)
endif
ifndef TABLE
	$(error TABLE is not set. please use `make {XXX} TABLE=<YOUR_PREFIX>.`)
endif

.check-args:
ifndef AWS_REGION
	$(error AWS_REGION is not set. please use `make {XXX} AWS_REGION=<YOUR_PREFIX>.`)
endif
ifndef AWS_ACCOUNT_ID
	$(error AWS_ACCOUNT_ID is not set. please use `make {XXX} AWS_ACCOUNT_ID=<YOUR_PREFIX>.`)
endif

# ------------------------------------------------------------------------------
# Build and Push All Platform Containers
# ------------------------------------------------------------------------------

build-containers-release: .check-args
	$(info *** build and upload containers to AWS ECR)
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	@for container in $(CONTAINERS); do \
		echo "building $$container" ; \
		docker build -t $(CONTAINERS_PREFIX)-$$container $(CONTAINERS_DIR)/$$container/. ;\
		docker tag $(CONTAINERS_PREFIX)-$$container:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(CONTAINERS_PREFIX)-$$container:latest ; \
		docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(CONTAINERS_PREFIX)-$$container:latest ; \
	done

# ------------------------------------------------------------------------------
# Built Ottr Router Lambda
# ------------------------------------------------------------------------------

build-otter-router: .check-args
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker build -t otter-infrastructure:router otter/router/.
	docker tag otter-infrastructure:router $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/otter-infrastructure:router ; \
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/otter-infrastructure:router ; \

# ------------------------------------------------------------------------------
# Build Ottr Handler Lambda
# ------------------------------------------------------------------------------

build-otter-handler: .check-args
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker build -t otter-infrastructure:handler otter/handler/.
	docker tag otter-infrastructure:handler $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/otter-infrastructure:handler ; \
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/otter-infrastructure:handler ; \

# ------------------------------------------------------------------------------
# Build Ottr API
# ------------------------------------------------------------------------------

build-api: .check-api-args
	$(info *** build and upload containers to AWS ECR)
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	AWS_REGION=${AWS_REGION} AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID} TABLE=${TABLE} PREFIX=${PREFIX} docker-compose -f api/docker-compose.yaml build

# API Server Image
	docker tag otter-api:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/otter-acme-api:server
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/otter-acme-api:server
# Envoy Sidecar Image
	docker tag otter-envoy:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/otter-acme-api:envoy
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/otter-acme-api:envoy

	aws ecs update-service --cluster otter --service otter-api-service --force-new-deployment

# ------------------------------------------------------------------------------
# Platform Specific Containers
# ------------------------------------------------------------------------------

build-panos-8.x: .check-args
	$(info *** build and upload containers to AWS ECR)
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker build -t $(CONTAINERS_PREFIX)-panos-8.x:latest $(CONTAINERS_DIR)/panos-8.x/.
	docker tag $(CONTAINERS_PREFIX)-panos-8.x:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(CONTAINERS_PREFIX)-panos-8.x:latest ; \
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(CONTAINERS_PREFIX)-panos-8.x:latest ; \

build-panos-9.x: .check-args
	$(info *** build and upload containers to AWS ECR)
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker build -t $(CONTAINERS_PREFIX)-panos-9.x:latest $(CONTAINERS_DIR)/panos-9.x/.
	docker tag $(CONTAINERS_PREFIX)-panos-9.x:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(CONTAINERS_PREFIX)-panos-9.x:latest ; \
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(CONTAINERS_PREFIX)-panos-9.x:latest ; \

build-f5-14.x: .check-args
	$(info *** build and upload containers to AWS ECR)
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker build -t $(CONTAINERS_PREFIX)-f5-14.x:latest $(CONTAINERS_DIR)/f5-14.x/.
	docker tag $(CONTAINERS_PREFIX)-f5-14.x:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(CONTAINERS_PREFIX)-f5-14.x:latest ; \
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(CONTAINERS_PREFIX)-f5-14.x:latest ; \

build-lighthouse-21.x: .check-args
	$(info *** build and upload containers to AWS ECR)
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker build -t $(CONTAINERS_PREFIX)-lighthouse-21.x:latest $(CONTAINERS_DIR)/lighthouse-21.x/.
	docker tag $(CONTAINERS_PREFIX)-lighthouse-21.x:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(CONTAINERS_PREFIX)-lighthouse-21.x:latest ; \
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(CONTAINERS_PREFIX)-lighthouse-21.x:latest ; \

build-linux-aws-ssm: .check-args
	$(info *** build and upload containers to AWS ECR)
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker build -t $(CONTAINERS_PREFIX)-linux-aws-ssm:latest $(CONTAINERS_DIR)/linux-aws-ssm/.
	docker tag $(CONTAINERS_PREFIX)-linux-aws-ssm:latest $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(CONTAINERS_PREFIX)-linux-aws-ssm:latest ; \
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(CONTAINERS_PREFIX)-linux-aws-ssm:latest ; \

# .PHONY:build-containers-release
