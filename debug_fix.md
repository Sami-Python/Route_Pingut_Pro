# Debug Log
Error mounting APIs: No module named 'google.oauth2'

Traceback:
```
Traceback (most recent call last):
  File "C:\Users\samih\code\pingut-projekti-4\api_server.py", line 124, in <module>
    from gcal_api import app as gcal_app
  File "C:\Users\samih\code\pingut-projekti-4\api\gcal_api.py", line 5, in <module>
    from google.oauth2.credentials import Credentials
ModuleNotFoundError: No module named 'google.oauth2'

```

Sys.path:
['C:\\Users\\samih\\code\\pingut-projekti-4', 'C:\\Users\\samih\\AppData\\Local\\Programs\\Python\\Python312\\python312.zip', 'C:\\Users\\samih\\AppData\\Local\\Programs\\Python\\Python312\\DLLs', 'C:\\Users\\samih\\AppData\\Local\\Programs\\Python\\Python312\\Lib', 'C:\\Users\\samih\\AppData\\Local\\Programs\\Python\\Python312', 'C:\\Users\\samih\\code\\pingut-projekti-4\\.venv', 'C:\\Users\\samih\\code\\pingut-projekti-4\\.venv\\Lib\\site-packages', 'C:\\Users\\samih\\code\\pingut-projekti-4\\api', 'C:\\Users\\samih\\code\\pingut-projekti-4\\api']
