# Real Estate Django App

Simple real estate listings app built with Django. Features:

- Listings with categories (sale/rent/buy)
- Listing detail and search
- User registration/login and profile
- Inquiries and admin notifications
- Multi-image listings (Photo model)
- Paystack payment integration (test keys)

To run locally:

```bash
python -m venv venv
venv\Scripts\Activate.ps1  # on Windows PowerShell
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

For deployment (Render/Gunicorn) the `Procfile` is provided.
