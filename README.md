# Website Wrappers

## How to run wrappers:

| :exclamation:  Make sure the respective External Service is running  |
|----------------------------------------------------------------------|

- Example: Zooking Wrapper 
```bash
python -m Wrappers.zooking.zooking_regular_handler; 
python -m Wrappers.zooking.zooking_scheduled_handler;
```


## Testing:

Some tests require **External Services** to be running (`tests/test_api_schemas.py`).

```bash
cd tests/ # make sure you are in this folder
pytest
```