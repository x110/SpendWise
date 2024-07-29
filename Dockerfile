# read the doc: https://huggingface.co/docs/hub/spaces-sdks-docker
# you will also find guides on how best to write your Dockerfile

FROM python:3.9

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user . /app
# Run the bot
# Use a script to run the appropriate command
COPY --chown=user start.sh /app/start.sh
# Set the PYTHONPATH environment variable
ENV PYTHONPATH=/app/src
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
