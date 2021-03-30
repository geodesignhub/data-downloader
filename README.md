# Geodesignhub Data Downloader

This is a script uses the [Geodesignhub API](https://www.geodesignhub.com/api/) to download the design synthesis as GeoJSON and save it as a Geopackage or other vector geo-spatial data formats.

## Install dependencies

To install the required libraries use the following command, this assumes Python 3 and is not tested on Python 2.

```
pip install -r requirements.txt
```

## 3-step process

1. Open ```config.json``` in a text editor such as notepad etc. and fill in the project ID and API Token.
2. Enter your project ID and [Geodeisgnhub API Token](https://www.geodesignhub.com/api/token). (You can your token by going to the link).
3. Run ```python download_data.py``` and follow the instructions to download a design synthesis or diagram data.
