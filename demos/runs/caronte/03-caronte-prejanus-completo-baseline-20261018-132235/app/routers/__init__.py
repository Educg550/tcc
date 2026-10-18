from . import auth, edicts, forms, submissions  # noqa: F401

all_routers = [auth.router, forms.router, edicts.router, submissions.router]