# Website Wrappers

## How to run wrappers:

| :exclamation:  Make sure the respective External Service is running  |
|----------------------------------------------------------------------|

- Example: Zooking Wrapper 
```bash
python -m Wrappers.zooking.zooking_regular_handler; # runs regular wrapper
python -m Wrappers.zooking.zooking_scheduled_handler; # runs scheduled events handling wrapper
```

The same thing applies to wrappers of the other external services, simply change `zooking` to `earthstayin` or `clickandgo`.


## Testing:

Some tests require **External Services** to be running (`tests/test_api_schema_zooking.py`).

```bash
cd tests/ # make sure you are in this folder
pytest
```