def hello_world():
    print "Hello World!"

class Sample1(object):
    """Article ingestion workflow for Literature collection."""
    name = "record-v1.0.0"
    data_type = "hep"


    workflow = (
        hello_world
    )
