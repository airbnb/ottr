FROM public.ecr.aws/lambda/python:3.8

COPY src ${LAMBDA_TASK_ROOT}
RUN chmod 644 $(find ${LAMBDA_TASK_ROOT} -type f)
RUN chmod 755 $(find ${LAMBDA_TASK_ROOT} -type d)

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

LABEL maintainer="Kenneth Yang <kenneth.yang@airbnb.com>" \
    version="1.0.0"

CMD ["handler.main"]