import logging
import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# Nom du service (apparaît dans Signoz)
SERVICE_NAME = "arteci-api"

# Adresse du collecteur OpenTelemetry (Signoz)
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")


def setup_tracing():
    # Identité du service
    resource = Resource.create({"service.name": SERVICE_NAME})

    # Fournisseur de traces
    provider = TracerProvider(resource=resource)

    # Export vers Signoz (OTLP)
    exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    return trace.get_tracer(SERVICE_NAME)


def setup_logging():
    # Logs structurés : timestamp | niveau | service | message
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(SERVICE_NAME)