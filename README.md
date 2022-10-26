# HOW TO RUN THIS PROJECT

1. Create a virtual environment (not compulsory but recommended)
```bash
python -m venv [name_of_virtual_environment]
```
2. New folder will be created. Move to that folder in Terminal and Execute the following Command :

```bash
pip install -r requirements.txt
```
3. Git clone the project
4. Move to the project folder in Terminal. Then run the following Commands :

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

5. Now enter following URL in Your Browser Installed On Your PC
http://127.0.0.1:8000/