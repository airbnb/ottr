resource "aws_cloudwatch_event_rule" "otter" {
  name                = "otter"
  description         = "CloudWatch Trigger "
  schedule_expression = var.cloudwatch_schedule
}

resource "aws_cloudwatch_event_target" "otter" {
  rule      = aws_cloudwatch_event_rule.otter.name
  target_id = "otter"
  arn       = aws_lambda_function.otter.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_otter" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.otter.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.otter.arn
}
