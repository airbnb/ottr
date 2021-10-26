resource "aws_dynamodb_table" "otter" {
  name           = var.database
  billing_mode   = "PAY_PER_REQUEST"
  read_capacity  = 10
  write_capacity = 10
  hash_key       = "system_name"

  server_side_encryption {
    enabled = true
  }

  attribute {
    name = "ip_address"
    type = "S"
  }

  attribute {
    name = "system_name"
    type = "S"
  }

  attribute {
    name = "data_center"
    type = "S"
  }

  attribute {
    name = "host_platform"
    type = "S"
  }

  attribute {
    name = "origin"
    type = "S"
  }

  global_secondary_index {
    name            = "ip_address_index"
    hash_key        = "ip_address"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "system_name_index"
    hash_key        = "system_name"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "data_center_index"
    hash_key        = "data_center"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "host_platform_index"
    hash_key        = "host_platform"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "origin_index"
    hash_key        = "origin"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }
}
