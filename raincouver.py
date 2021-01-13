import requests
import json
import os
from lib.utils.env import load_params, set_env
from lib.utils.usgs import UsgsRequest


def main(params):
    usgs_request = UsgsRequest(params=params)
    usgs_request.login()
    usgs_request.search_dataset()
    usgs_request.scene_search()
    usgs_request.retrieve_scenes_downloads()
    usgs_request.download_images()


if __name__ == '__main__':
    print(os.path.dirname(os.path.realpath(__file__)))
    set_env(project_path=os.path.dirname(os.path.realpath(__file__)))
    params = load_params()
    main(params=params)
