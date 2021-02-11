import os
from lib.utils.env import load_params, set_env
from lib.utils.usgs import UsgsRequest
from preprocess.image_process import ImageProcessor


def main(params):
    # Satellite image downloads
    if params['DOWNLOAD_SAT']:
        usgs_request = UsgsRequest(params=params)
        usgs_request.run()

    # Image processing
    if params['PROCESS_IMGS']:
        sat_images = ImageProcessor(params=params)
        sat_images.run()


if __name__ == '__main__':
    print(os.path.dirname(os.path.realpath(__file__)))
    set_env(project_path=os.path.dirname(os.path.realpath(__file__)))
    params = load_params()
    main(params=params)
