from apps.partners.models import Transactions


def create_transaction(**kwargs):
    return Transactions.objects.create(**kwargs)
