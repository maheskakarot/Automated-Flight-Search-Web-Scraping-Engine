import logging

db_default_formatter = logging.Formatter()


class ElasticSearchLogHandler(logging.Handler):
    def emit(self, record):
        try:
            from .elasticsearch import es, index
            document = record.__dict__
            for key, value in document.items():
                if type(value) not in [int, float, str, list]:
                    document[key]: str(value)
            es.index(index=index, document=document)
        except:
            pass
