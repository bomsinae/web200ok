import os
import django


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    from monitor.models import Http

    qs = Http.objects.exclude(url__startswith='http')
    count = qs.count()
    for obj in qs:
        print(f"Deleting: {obj.url}")
        obj.delete()
    print(f"Deleted {count} records.")


if __name__ == '__main__':
    main()
