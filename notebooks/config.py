import multiprocessing as mp

############ Common ############
NO_OF_PROCESSORS = mp.cpu_count()
COMPARTMENT_ID = "ocid1.compartment.oc1..aaaaaaaanjtbllhqxcg67dq7em3vto2mvsbc6pbgk4pw6cx37afzk3tngmoa"
NAMESPACE = "orasejapan"

############ 01. Getting Started ############
BUCKET_NAME = "ai-bbs-vision"
PRETRAINED_MODEL_TEST_IMAGE_PATH = "./images"

############ 02. Custom Model ############
LEMON_TRAINING_DATA_BUCKET_NAME = "lemon-training-data-bucket"
DATASET_PREFIX = ["bad_quality", "empty_background", "good_quality"]
LEMON_DATASET_DIRECTORY_PATH = "./lemon_dataset"
LABEL_MAP = {"bad_quality/": "bad_quality", "empty_background/": "empty_background", "good_quality/": "good_quality"}
