import requests
import json

from lib.utils.env import load_params
from lib.utils.usgs import UsgsRequest


def main(params):
    usgs_request = UsgsRequest(params=params)
    usgs_request.login()
    usgs_request.search_dataset()
    usgs_request.scene_search()
    usgs_request.download_scenes()


if __name__ == '__main__':
    params = load_params()
    main(params=params)
