FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN addgroup --system compendium && adduser --system --ingroup compendium compendium     && mkdir -p /data/assets/originals /data/assets/thumbnails     && chown -R compendium:compendium /data /app
COPY pyproject.toml README.md ./
COPY app ./app
COPY scripts ./scripts
COPY tests ./tests
RUN pip install --no-cache-dir .
USER compendium
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
