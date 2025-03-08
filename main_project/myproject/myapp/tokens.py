from django.contrib.auth.tokens import default_token_generator


def generate_activation_token(user):
    return default_token_generator.make_token(user)
