import logging
import os
import sys
import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import \
    OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import \
    OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.instrumentation.ollama import OllamaInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


log = logging.getLogger(__name__)

class JsonFormatter(logging.Formatter):
    def format(self, record) -> str:
        log_record = {
            "timestamp": record.created,
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "pathname": record.pathname,
            "lineno": record.lineno,
        }
        return json.dumps(log_record)

def setup_otel_instrumentation() -> None:
    try:
        OllamaInstrumentor().instrument()
    except Exception as error:
        logging.error(f"Instrumentation setup failed. Error: {error}")


def setup_otel_logging(log: logging.Logger) -> None:
    instance_id = os.getenv("POD_NAME", 1)
    resource = Resource.create(
        {
            "service.name": "blog_builder",
            "service.instance.id": f"blog_builder-{instance_id}",
        }
    )
    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)

    exporter = OTLPLogExporter(
        endpoint="host.containers.internal:6831", insecure=True
    )

    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)

    app.logger.addHandler(handler)


def setup_otel_tracing() -> trace:
    resource = Resource.create(
        {
            "service.name": "blog_builder",
            "service.instance.id": os.getenv("POD_NAME", "Undefined"),
            "k8s.pod.name": os.getenv("POD_NAME", "Undefined"),
            "k8s.namespace.name": os.getenv("POD_NAMESPACE", "Undefined"),
            "k8s.pod.ip": os.getenv("POD_IP", "Undefined"),
            "k8s.node.name": os.getenv("NODE_NAME", "Undefined"),
        }
    )
    trace.set_tracer_provider(TracerProvider(resource=resource))

    otlp_tracing_exporter = OTLPSpanExporter(
        endpoint="host.containers.internal:6831",
        insecure=True,
    )
    trace.get_tracer_provider().add_span_processor(
        SimpleSpanProcessor(otlp_tracing_exporter)
    )
    return trace


def setup_otel_metrics() -> tuple:
    instance_id = os.getenv("POD_NAME", 1)
    resource = Resource.create(
        {
            "service.name": "blog_builder",
            "service.instance.id": f"blog_builder-{instance_id}",
        }
    )
    metric_exporter = OTLPMetricExporter(
        endpoint="host.containers.internal:6831",
        insecure=True,
    )
    reader = PeriodicExportingMetricReader(
        exporter=metric_exporter,
        export_interval_millis=3000.0,
        export_timeout_millis=5000.0,
    )
    meter_provider = MeterProvider(metric_readers=[reader], resource=resource)
    metrics.set_meter_provider(meter_provider)
    meter = metrics.get_meter(__name__)
    counter = meter.create_counter(
        name="requests", description="Number of requests", unit="1"
    )
    return metrics, counter




def evaluate_prompt(message: str, system_prompt: str) -> str | None:
    model = None
    result = {}
    output = None
    try:
        model = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "gemma4"),
            base_url=os.getenv(
                "OLLAMA_BASE_URL", "http://host.containers.internal:11434"
            ),
            temperature=0,
        )
    except Exception as error:
        log.error(f"No model was created, error: {error}")
        return

    if model:
        setup_otel_instrumentation()
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=message)]
        try:
            result = model.invoke(messages)
        except Exception as error:
            log.error(f"No response was given, error: {error}")
            return

        if result and isinstance(result, AIMessage):
            try:
                output = result.content
            except AttributeError as error:
                log.error(f"No AI message was received, error: {error}")
        else:
            log.error(f"Malformed response was received: {result}")
    return output


if __name__ == "__main__":
    filename = sys.argv[1]

    try:
        with open("./base_prompt.md") as b:
            base_prompt = b.read()
    except OSError as error:
        log.error(f"Could not read base prompt, error: {error}")
        base_prompt = "You are a useful expert"

    system_prompt = base_prompt
    try:
        with open(filename) as f:
            content = f.read()
            if content:
                message = (
                    f"for the file {filename}, perform a spellcheck and validate its grammar on its content:\n"
                    f"=START=\n{content}\n=END="
                )
                response = evaluate_prompt(
                    message=message,
                    system_prompt=system_prompt,
                )
                if response:
                    print(response)
    except IOError:
        log.error(f"File {filename} could not be read")
