## Developer Docs

### Overview of project structure
```
pep_gui/
├── tests/                               # tests for pep_gui
│   ├── config.ini                       # test configuration required for running kwiver runner tests
│   └── tests...
├── src/                       
│   ├── pep_tk/
│   │   ├── core/                        # backend functionality for pep_tk
│   │   │   ├── configuration/           # reading pipeline manifest and other configurations
│   │   │   ├── kwiver/                  # code for running kwiver pipelinees and compiling pipeleins     
│   │   │   ├── parser/                  # for parsing user supplied dataset manifests in different formats
│   │   │   ├── utilities/               # miscellaneous utilities
│   │   │   ├── job.py                   # serializing, reading, and saving job state data
│   │   │   └── scheduler.py             # the scheduler which runs tasks and communicates progress/user interactions with the GUI
│   │   └─── psg/                        # user interface related code
│   │   │   ├── layouts/                 # components that exist within windows
│   │   │   ├── windows/                 # windows of the GUI application
│   │   │   ├── events/                  # event data and manager for communication with scheduler
│   │   │   └── settings.py              # GUI user-defined setting uitilities
│   │   ├──  conf/
│   │   │   ├── pipeline_manifest.yaml   # Pipeline manifest for defining pipelines for GUI to use.
│   │   │   └── pipelines/               # folder containing pipelines, models, etc..
│   │   ├──  lib/                        # folder containing icons/image resources
│   │   └──  launch.py                   # program entry point/launch script                              
└── ...

```



### Client/Backend communication

In `src/pep_tk/core/scheduler.py` there is an abstract class called `SchedulerEventManager` which is used by the scheduler to trigger
certain events that the client can then respond to.  These events are things like triggering an event that the task
started, or ended, or events pertaining to the outputs or progress of tasks.

The PySimpleGUI application has a class called `GUIManager` (in `src/psg/events/manager.py`) which implements 
`SchedulerEventManager` and defines the functionality specific to how the GUI responds to events. This means if someone 
wanted to completely scrap this GUI and make their own, you would just have to implement your own 
`SchedulerEventManager` with whatever functionality you want it to have.

The `GUIManager` creates instances of `ProgressGUIEventData` (in `src/psg/events/data.py`) which it then communicates to 
the PySimpleGUI window via `window.write_event_value`.  This allows the scheduler to pass information to the GUI which 
can then update progress bars, task statuses, etc...