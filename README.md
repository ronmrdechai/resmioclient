# ResmioClient
A Python client for Resmio's REST API. Currently only supports ordering seats.

## Usage

The `ResmioClient` object exports only one function, `request_seats`. Create a
`ResmioClient` object and pass it the name of your facility (Resmio asks you to
fill this in when you create a restaurant.). Then just call `requests_seats` and
your seats should be reserved.

```python
from resmioclient import ResmioClient
from datetime import datetime

client = ResmioClient("pizza-hut")
reference_num = client.request_seats(
        date=datetime(year=2015, month=12, day=31, hour=22),
        num=10)
print "Happy new year! Your invitation number is " + reference_num
```
