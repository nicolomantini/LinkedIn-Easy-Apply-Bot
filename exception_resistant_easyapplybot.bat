::  Once all the jobs had been applied to, this loop (as a process), will be terminated from the easyapplybot.py file
:start
python easyapplybot.py

:: wait 120 seconds between re-runs after an error. This is useful - will prevent captch challange in a worst case scenario.
timeout /t 120

:: goto looping statement, which will execute only after "python easyapplybot.py" quits, for example in case of an unhandled exception, which at this point in development - almost doesn't happen
goto start 