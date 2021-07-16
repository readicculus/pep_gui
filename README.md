# PEP-TK
#### Table of Contents
  * [Terminology](#terminology)
  * [The GUI](#the-gui)
    + [- Configuring the application preferences -](#--configuring-the-application-preferences--)
    + [- Creating a Job -](#--creating-a-job--)
    + [- Resuming a job -](#--resuming-a-job--)
    + [- Job progress -](#--job-progress--)
    + [- Job outputs -](#--job-outputs--)
      - [Pipeline outputs (processed image lists/detections)](#pipeline-outputs--processed-image-lists-detections-)
      - [Logs](#logs)
  * [Dataset Manifest](#dataset-manifest)
    + [- Dataset attributes -](#--dataset-attributes--)
    + [- Example 1 (Basics) -](#--example-1--basics---)
    + [- Example 2 (arbitrary hierarchy/organization) -](#--example-2--arbitrary-hierarchy-organization---)
  * [Additional features](#additional-features)
  * [Future features](#future-features)


#### Terminology
 - **Task** - a task is a unit of work in the GUI and is comprised of running a single dataset through a pipeline.
 - **Job** - a job is one or more tasks, so a job is comprised of running one or more datasets through a pipeline.

## The GUI


### - Configuring the application preferences -
When the application is launched for the first time you will be prompted to configure the following properties.
After that, to modify these properties, go to `File > Properties`.
Here you can set:
- Which SEAL-TK directory to use.
- Which dataset manfieset file to use.
- The base directory for jobs (new jobs will be created in `/path/to/job_base_dir/`)

![preoperties_window.png](lib/img/screenshots/preoperties_window.png)
### - Creating a Job -
<img src="lib/img/screenshots/create_job.png" width="75%" height="75%">
When you first launch the program you will be brought to a page to create a job.  To create a job:
1. Select which datasets you want to run
2. Select which pipeline to use
3. Select a unique name for your job

### - Resuming a job -
Resuming a job is usefil if for some reason the GUI or machine you are on crashes mid-job.  In addition if for some reason you were to cancel some tasks in a job, and decide you want to run them later, resuming will re-run any cancelled tasks.
To resume a Job click File > Resume Job which will open a prompt to select a folder.  Select the folder of the job you would like to resume.

_Since a task is the smallest unit of work, if a task fails half way through, resuming a job will re-run that task from the beginning.  If a task is successful resuming a job will not re-run that task._ 

### - Job progress -
<img src="lib/img/screenshots/progress_window.png" width="75%" height="75%">

The job progress GUI allows you to track individual task's progress, to cancel a task, and to see metrics such as frames/sec and estimated time to completion.
### - Job outputs -
#### Pipeline outputs (processed image lists/detections)
1. When a task is running, the task's outputs will be written to `job_base_dir/job_name/outputs_pending/`.
2. When a task is cancelled or an error occurs the task's output files will be moved to `job_base_dir/job_name/outputs_error/`.
3. When a task is successfully completed the task's output files will be moved to  `job_base_dir/job_name/outputs_success/`.
#### Logs
The `job_base_dir/job_name/logs/` directory contains the underlying kwiver outputs and application logs which are helpful for debugging purposes


## Dataset Manifest
The dataset manifest is a file that defines all of the datasets available in yaml format.  When creating a job you will be able to select and filter which datasets from the dataset manifest to run.

This format allows us to organize datasets as arbitrary hierarchies.  

### - Dataset attributes -
Currently a dataset must have one or more of the following attributes:
- `color_image_list` - the color image list txt file
- `thermal_image_list` - the thermal image list txt file
    
Additional optional attributes are:
- `transformation_file` - the .h5 transformation file

### - Example 1 (Basics) -
For example we could seperate things into categories by survey.
```yaml
Datasets:
  Kotz-2019:
    fl04:
      CENT:
        thermal_image_list: /path/to/kotz/fl04/CENT/thermal_images.txt
        color_image_list: /path/to/kotz/fl04/CENT/color_images.txt
        transformation_file: /path/to/Homographies/A90_RGB-IR_C_100mm_0deg_20190509_fl4.h5
      LEFT:
        thermal_image_list: /path/to/kotz/fl04/LEFT/thermal_images.txt
        color_image_list: /path/to/kotz/fl04/LEFT/color_images.txt
        transformation_file: /path/to/Homographies/A90_RGB-IR_L_100mm_25deg_20190509-11_fl4-7.h5
  JoBSS:
    fl01:
      CENT:
        thermal_image_list: /path/to/jobss/fl01/CENT/thermal_images.txt
        color_image_list: /path/to/jobss/fl01/CENT/color_images.txt
        transformation_file: /path/to/Homographies/A90_RGB-IR_C_100mm_0deg_20190509_fl4.h5
      LEFT:
        thermal_image_list: /path/to/jobss/fl01/LEFT/thermal_images.txt
        color_image_list: /path/to/jobss/fl01/LEFT/color_images.txt
        transformation_file: /path/to/Homographies/A90_RGB-IR_L_100mm_25deg_20190509-11_fl4-7.h5
```
This example defines 4 datasets which we can select from in the GUI for running pipelines.
```
Kotz-2019:fl04:CENT
Kotz-2019:fl04:LEFT
JoBSS:fl01:LEFT
JoBSS:fl01:LEFT
```

### - Example 2 (arbitrary hierarchy/organization) -
The depth and organization of datasets is arbitrary.  
When the system see's any of the dataset attributes (`thermal_image_list`, `color_image_list`, etc..) it will know the group is a dataset and not a hierarchy.
For example, we can use this to define datasets for test imagery and to keep it seperate from our normal dataset of non-test images.
```yaml
Datasets:
  Kotz-2019:
    fl04:
      CENT:
        thermal_image_list: /path/to/kotz/fl04/CENT/thermal_images.txt
        color_image_list: /path/to/kotz/fl04/CENT/color_images.txt
        transformation_file: /path/to/Homographies/A90_RGB-IR_C_100mm_0deg_20190509_fl4.h5

  Polar-Bear-Dataset:
    thermal_image_list: /path/to/polarbears/thermal_images.txt
    color_image_list: /path/to/polarbears/color_images.txt

  test-data:
      Kotz-2019:
        fl04:
          CENT:
            thermal_image_list: /path/to/kotz/fl04/CENT/thermal_images_test.txt
            color_image_list: /path/to/kotz/fl04/CENT/color_images_test.txt
            transformation_file: /path/to/Homographies/A90_RGB-IR_C_100mm_0deg_20190509_fl4.h5
            
      Polar-Bear-Dataset:
        thermal_image_list: /path/to/polarbears/thermal_images_test.txt
        color_image_list: /path/to/polarbears/color_images_test.txt
```
This example defines 4 datasets which we can select from in the GUI for running pipelines.
```
Kotz-2019:fl04:CENT
Polar-Bear-Dataset
test-data:Kotz-2019:fl04:CENT
test-data:Polar-Bear-Dataset
```


#### Additional features
 - Can use absolute paths or relative paths.  If using relative paths, files are relative to the dataset manifest location.
 - If a dataset does not define a `transformation_file` the GUI will warn you if you try to use that dataset with a pipeline that requires a transformation (ex. subregion trigger)
#### Future features
  - Ability to define a set of images using wildcards instead of having to define an image list. ex `thermal_image_list: /path/to/kotz/fl04/CENT/*_ir.tif`
  - I want to add a GUI for helping validate a dataset manifest and to point user to where errors are in the yaml file.

