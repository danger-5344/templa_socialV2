# TemplaSocial — Email Template Manager & Social App (Django)

A Django 5 project that lets users:
- Create private/public email templates with `{{placeholders}}`
- Browse and use public templates
- Fill personalized fields dynamically (auto-detected from template)
- Build CTA links by combining an **Offer Link** (admin-managed) with **Tracking Parameter** sets
- Attribute templates to a **Platform** (choose from dropdown or add a new one)
- Admins can **create/update/delete** Offer Links and manage Networks/Offers. Non-admin users can use those links but cannot edit them.

## Quickstart

```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/

- Admin: http://127.0.0.1:8000/admin/
- Create a superuser to manage **Offer Links**, **Networks**, **Offers**, etc.

## Apps

- `accounts` – user signup/login; extends Django User lightly
- `catalog` – Platforms, TrackingParamSet, OfferNetwork, Offer, OfferLink (admin-only CRUD for OfferLink)
- `emails` – EmailTemplate CRUD & "Use Template" workflow

## Notes

- Placeholders use `{{like_this}}` syntax. They’re auto-detected on the Use page.
- CTA Builder concatenates selected Offer Link URL with chosen TrackingParamSet (URL-encoded query params).
- Non-admin users *cannot* access Offer Link CRUD via UI; that menu is hidden and server-protected.