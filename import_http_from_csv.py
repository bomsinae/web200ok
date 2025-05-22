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
            account_name = row['Account.name'].strip()
            zone_name = row['Zone.name'].strip()
            use_flag = row['Zone.cname'].strip().upper()

            if not zone_name or not account_name:
                continue
            if use_flag == 'YES':
                is_active = True
            elif use_flag == 'NO':
                # 이미 등록된 Http가 있으면 삭제
                url = f"https://{zone_name}"
                qs = Http.objects.filter(url=url)
                if qs.exists():
                    print(f"Deleting (NO): {url}")
                    qs.delete()
                continue
            else:
                continue

            if not zone_name or zone_name.endswith('sds-secaas.com'):
                continue

            try:
                account = Account.objects.get(name=account_name)
            except Account.DoesNotExist:
                print(f"Account not found: {account_name}")
                continue

            url = f"https://{zone_name}"

            # 중복 URL 방지
            if Http.objects.filter(label=zone_name).exists():
                print(f"Already exists: {url}")
                continue

            http = Http(
                account=account,
                url=url,
                label=zone_name,
                max_response_time=10,
                is_active=is_active
            )
            http.save()
            print(f"Created: {url} for {account_name} (is_active={is_active})")


if __name__ == '__main__':
    main()
