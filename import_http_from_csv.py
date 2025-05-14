import csv
import os
import django


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    from cf_account.models import Account
    from monitor.models import Http

    csv_path = os.path.join(os.path.dirname(__file__), 'tmp/all_zones.csv')
    print(csv_path)
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            account_name = row['Account'].strip()
            url = row['Zone'].strip()
            use_flag = row['CNAME'].strip().upper()

            if not url or not account_name:
                continue
            if use_flag == 'YES':
                is_active = True
            elif use_flag == 'NO':
                is_active = False
            else:
                continue

            if not url or url.endswith('sds-secaas.com'):
                continue

            try:
                account = Account.objects.get(name=account_name)
            except Account.DoesNotExist:
                print(f"Account not found: {account_name}")
                continue

            url = (f"https://{url}") if not url.startswith(('http://', 'https://')) else url

            # 중복 URL 방지
            if Http.objects.filter(url=url).exists():
                print(f"Already exists: {url}")
                continue

            http = Http(
                account=account,
                url=url,
                label=url,
                max_response_time=3,
                is_active=is_active
            )
            http.save()
            print(f"Created: {url} for {account_name} (is_active={is_active})")


if __name__ == '__main__':
    main()
